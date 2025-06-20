from datetime import datetime, date
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import transaction
from .models import *
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from .models import BMCAgreement
from PyPDF2 import PdfReader, PdfWriter
from django.core.files.base import ContentFile
import io
import os
import tempfile
import shutil
from datetime import datetime, date
from django.db import transaction
import os
from .models import BMCAgreement
from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import BMCAgreement
from PyPDF2 import PdfReader, PdfWriter
from django.core.files.base import ContentFile
import io
import os
from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt
from dateutil.relativedelta import relativedelta

# A utility function to get the number of months remaining to tell user how many months have left to expire.
def months_between_today_and_end(end_date):
    if not end_date:
        return "-"
    today = date.today()
    if end_date < today:
        return 0
    months = (end_date.year - today.year) * 12 + (end_date.month - today.month)
    if end_date.day < today.day:
        months -= 1
    return months


# Function to create amc agreement
def amc_create(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Get all required fields from POST
                product = request.POST.get("product")
                contractor = request.POST.get("contractor")
                pan = request.POST.get("pan")
                type_of_agreement = request.POST.get("type_of_agreement")
                agreement_date = request.POST.get("agreement_date")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")
                tenure_months = request.POST.get("tenure_months")
                lock_in_period = request.POST.get("lock_in_period")
                monthly_payout = request.POST.get("monthly_payout")
                document_status = request.POST.get("document_status")
                document_pending = request.POST.get("document_pending")
                document_file = request.FILES.get("document")

                # Parse dates
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

                # Determine if agreement is expired
                today = date.today()
                is_expired = end_date_obj and end_date_obj < today

                # Set base folder: "Ongoing" or "Expired"
                base_folder = "Expired" if is_expired else "Ongoing"

                # Agreement type folder
                agreement_type_folder = "AMC Agreements"

                # Use status as a folder (COMPLETE/INCOMPLETE/EXPIRED)
                status_folder = document_status.upper() if document_status else "UNKNOWN"

                # Agreement name from product (or file name if you prefer)
                agreement_name = product.strip() if product else (os.path.splitext(document_file.name)[0] if document_file else "UnknownAgreement")

                # Date folder
                date_folder = f"{start_date}-{end_date}"

                # File name (use product as file name if possible)
                file_base_name = f"{agreement_name}.pdf" if document_file else "document.pdf"

                # Build the full path: Agreements/Ongoing/AMC Agreements/STATUS/AGREEMENT_NAME/STARTDATE-ENDDATE/AGREEMENT_NAME.pdf
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )

                # Ensure the folder exists in MEDIA_ROOT
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                os.makedirs(full_upload_path, exist_ok=True)

                # Save the file to the correct location
                if document_file:
                    file_path = os.path.join(upload_folder, file_base_name)
                    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    with open(absolute_file_path, 'wb+') as destination:
                        for chunk in document_file.chunks():
                            destination.write(chunk)
                else:
                    file_path = None

                # Save the AMCAgreement instance with the correct document path and created_by user
                amc = AMCAgreement.objects.create(
                    product=product,
                    contractor=contractor,
                    pan=pan,
                    type_of_agreement=type_of_agreement,
                    agreement_date=agreement_date,
                    start_date=start_date,
                    end_date=end_date,
                    tenure_months=tenure_months,
                    lock_in_period=lock_in_period,
                    monthly_payout=monthly_payout,
                    document_status=document_status,
                    document_pending=document_pending,
                    document=file_path,  # Save relative path to the file
                    created_by=request.user if request.user.is_authenticated else None
                )
                print("Saved AMC Agreement:", amc)

            return HttpResponse("SUBMIT SUCCESSFULLY")
        except Exception as e:
            print("Error saving AMC Agreement:", e)
            return HttpResponse(f"Error: {e}", status=500)
    return HttpResponse("Only POST supported for now.")


# Function For merging the incomplete amc agreements 
@csrf_exempt
def amc_edit_merge(request, pk):
    """
    Merge a new PDF into the existing AMC agreement PDF.
    If the agreement is now expired (based on end_date), move the merged PDF to the Expired folder.
    If the status changes (e.g., INCOMPLETE -> COMPLETE), move the merged PDF to the new status folder and remove the old status folder if empty.
    The folder structure is maintained as:
    Agreements/{Ongoing|Expired}/AMC Agreements/{STATUS}/{Agreement Name}/{STARTDATE}-{ENDDATE}/
    """
    if request.method == "POST":
        print("---- amc_edit_merge POST ----")
        print("request.POST:", request.POST)
        print("request.FILES:", request.FILES)
        amc = get_object_or_404(AMCAgreement, pk=pk)
        print(f"Fetched AMCAgreement ID {pk}: {amc}")

        # Get new values from request
        new_status = request.POST.get("document_status", amc.document_status)
        print("New status:", new_status)
        new_pending_document = request.POST.get("pending_document", amc.document_pending)
        print("New pending_document:", new_pending_document)
        new_pdf_file = request.FILES.get("insert_pdf")
        print("New PDF file:", new_pdf_file.name if new_pdf_file else "None")

        if not new_pdf_file:
            print("No PDF uploaded")
            return JsonResponse({"error": "No PDF uploaded"}, status=400)

        temp_dir = None
        try:
            with transaction.atomic():
                # Verify we have an existing document
                if not amc.document:
                    print("Error: No existing document to merge with")
                    return JsonResponse({"error": "No existing document to merge with"}, status=400)

                existing_file_path = amc.document.path
                existing_filename = os.path.basename(amc.document.name)
                print(f"Existing file path: {existing_file_path}")
                print(f"Existing filename: {existing_filename}")

                # Initialize PDF writer for merged content
                writer = PdfWriter()
                print("Initialized PdfWriter for merging.")

                # Load existing PDF pages
                print("Loading existing PDF...")
                existing_pdf = PdfReader(existing_file_path)
                original_page_count = len(existing_pdf.pages)
                print(f"Existing PDF has {original_page_count} pages")
                
                # Add all existing pages
                for page in existing_pdf.pages:
                    writer.add_page(page)
                print(f"Added {original_page_count} existing pages to writer")

                # Load and add new PDF pages
                print("Loading new PDF to append...")
                new_pdf = PdfReader(new_pdf_file)
                new_page_count = len(new_pdf.pages)
                print(f"New PDF has {new_page_count} pages")
                
                for page in new_pdf.pages:
                    writer.add_page(page)
                print(f"Added {new_page_count} new pages to writer")

                # Write merged content to a temp file
                temp_dir = tempfile.mkdtemp()
                temp_pdf_path = os.path.join(temp_dir, existing_filename)
                with open(temp_pdf_path, 'wb') as temp_f:
                    writer.write(temp_f)
                print(f"Created merged PDF with {len(writer.pages)} total pages at {temp_pdf_path}")

                # Determine if agreement is now expired
                today = date.today()
                end_date_obj = amc.end_date if isinstance(amc.end_date, date) else datetime.strptime(str(amc.end_date), "%Y-%m-%d").date()
                is_expired = end_date_obj and end_date_obj < today

                # Build the correct folder structure
                base_folder = "Expired" if is_expired else "Ongoing"
                agreement_type_folder = "AMC Agreements"
                status_folder = new_status.upper() if new_status else "UNKNOWN"
                agreement_name = os.path.splitext(existing_filename)[0]
                date_folder = f"{amc.start_date}-{amc.end_date}"
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                new_file_path = os.path.join(full_upload_path, existing_filename)

                # Only now create the final folder and move the file
                os.makedirs(full_upload_path, exist_ok=True)
                shutil.move(temp_pdf_path, new_file_path)

                # Remove old file if it's in a different location
                if os.path.abspath(existing_file_path) != os.path.abspath(new_file_path):
                    print(f"Moving file from {existing_file_path} to {new_file_path}")
                    if os.path.exists(existing_file_path):
                        os.remove(existing_file_path)
                    # Clean up old empty folders up to status level
                    try:
                        old_date_folder = os.path.dirname(existing_file_path)
                        old_agreement_folder = os.path.dirname(old_date_folder)
                        old_status_folder = os.path.dirname(old_agreement_folder)
                        # Remove date folder if empty
                        if os.path.isdir(old_date_folder) and not os.listdir(old_date_folder):
                            os.rmdir(old_date_folder)
                        # Remove agreement folder if empty
                        if os.path.isdir(old_agreement_folder) and not os.listdir(old_agreement_folder):
                            os.rmdir(old_agreement_folder)
                        # Remove status folder if empty
                        if os.path.isdir(old_status_folder) and not os.listdir(old_status_folder):
                            os.rmdir(old_status_folder)
                    except Exception as cleanup_err:
                        print("Cleanup error:", cleanup_err)

                # Update the document field to the new relative path if location changed
                rel_file_path = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
                if amc.document.name != rel_file_path.replace("\\", "/"):
                    amc.document.name = rel_file_path.replace("\\", "/")

                # Update the model to reflect the changes
                amc.document_status = new_status
                amc.document_pending = new_pending_document
                amc.save()

                print("PDF successfully merged and saved with correct folder structure")
                print(f"Final file location: {new_file_path}")
                return JsonResponse({"success": True, "new_page_count": len(writer.pages)})

        except Exception as e:
            print("Exception during PDF merge:", str(e))
            # Clean up temp dir if exists
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            # Optionally, clean up any partially created folders/files in MEDIA_ROOT
            if 'full_upload_path' in locals() and os.path.exists(full_upload_path):
                try:
                    shutil.rmtree(full_upload_path)
                except Exception:
                    pass
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            # Always clean up temp dir
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    print("Request method not allowed:", request.method)
    return JsonResponse({"error": "Only POST allowed"}, status=405)


# Function for searching incomplete amc agreement for data entry user.
def amc_search(request):
    try:
        contractor = request.GET.get('contractor', '').strip()
        print("[amc_search] The user entered the contractor:", contractor)
        product = request.GET.get('product', '').strip()
        print("[amc_search] The user entered the product:", product)
        results = []
        if contractor and product:
            qs = AMCAgreement.objects.filter(
                contractor__iexact=contractor,
                product__iexact=product
            )
            print(f"[amc_search] Found {qs.count()} results for contractor '{contractor}' and product '{product}'")
            for amc in qs:
                doc_url = amc.document.url if amc.document else ""
                doc_name = amc.document.name if amc.document else ""
                doc_name_only = os.path.basename(doc_name) if doc_name else ""
                print(f"[amc_search] AMC ID: {amc.pk}, document.name: '{doc_name}', document.url: '{doc_url}', file name only: '{doc_name_only}'")
                results.append({
                    "id": amc.id,
                    "product": amc.product,
                    "contractor": amc.contractor,
                    "document_status": amc.document_status,
                    "document_pending": amc.document_pending,
                    "document_url": doc_url,
                    "document_name": doc_name_only,
                })
        print(f"[amc_search] Final data sent: {results}")
        return JsonResponse({"results": results})
    except Exception as e:
        print(f"[amc_search] Exception occurred: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# Function for searching amc agreement for a user whose role is viewer
def amc_search_viewer(request):
    try:
        contractor = request.GET.get('contractor', '').strip()
        product = request.GET.get('product', '').strip()
        status = request.GET.get('status', '').strip().upper()

        qs = AMCAgreement.objects.all()
        if status:
            qs = qs.filter(document_status__iexact=status)
        if contractor:
            qs = qs.filter(contractor__icontains=contractor)
        if product:
            qs = qs.filter(product__icontains=product)

        def format_dmy(date_obj):
            if not date_obj:
                return ""
            return date_obj.strftime("%d/%m/%y")

        results = []
        for obj in qs:
            start = obj.start_date
            end = obj.end_date
            expire_months = months_between_today_and_end(end) if end else "-"
            if obj.created_by:
                creator = f"{obj.created_by.first_name or ''} {obj.created_by.last_name or ''}".strip()
                if not creator:
                    creator = obj.created_by.email
            else:
                creator = ""
            results.append({
                "id": obj.id,
                "agreement_date": format_dmy(getattr(obj, "agreement_date", None)),
                "product": getattr(obj, "product", ""),
                "contractor": obj.contractor,
                "document_status": obj.document_status,
                "pending_document": getattr(obj, "document_pending", ""),
                "start_date": format_dmy(start) if start else "",
                "end_date": format_dmy(end) if end else "",
                "expire_months": expire_months,
                "created_by": creator,
                "document_url": obj.document.url if obj.document else "",
            })
        return JsonResponse({"results": results})
    except Exception as e:
        print(f"[amc_search_viewer] Exception occurred: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# Function for getting amc agreement status number of complete and incomplete agreement.
def amc_stats(request):
    total = AMCAgreement.objects.count()
    complete = AMCAgreement.objects.filter(document_status='COMPLETE').count()
    incomplete = AMCAgreement.objects.filter(document_status='INCOMPLETE').count()
    return JsonResponse({
        "total": total,
        "complete": complete,
        "incomplete": incomplete
    })

# ------------------ALL FUNCTION FOR AMC AGREEMENT ENDS HERE----------------

# A FUNCTION FOR CREATING THE BMC AGREEMENTS (BY DATA ENTRY USER)
def bmc_create(request):
    if request.method == "POST":
        temp_dir = None
        full_upload_path = None
        try:
            with transaction.atomic():
                # Get all required fields from POST
                zone = request.POST.get("zone")
                location = request.POST.get("location")
                contractor = request.POST.get("contractor")
                pan = request.POST.get("pan")
                type_of_agreement = request.POST.get("type_of_agreement")
                agreement_date = request.POST.get("agreement_date")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")
                tenure_months = request.POST.get("tenure_months")
                lock_in_period = request.POST.get("lock_in_period")
                monthly_payout = request.POST.get("monthly_payout")
                document_status = request.POST.get("document_status")
                document_pending = request.POST.get("document_pending")
                document_file = request.FILES.get("document")

                # Parse dates
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

                # Determine if agreement is expired
                today = date.today()
                is_expired = end_date_obj and end_date_obj < today

                # Set base folder: "Ongoing" or "Expired"
                base_folder = "Expired" if is_expired else "Ongoing"
                agreement_type_folder = "BMC Agreements"
                status_folder = document_status.upper() if document_status else "UNKNOWN"
                agreement_name = location.strip() if location else (os.path.splitext(document_file.name)[0] if document_file else "UnknownAgreement")
                date_folder = f"{start_date}-{end_date}"
                file_base_name = f"{agreement_name}.pdf" if document_file else "document.pdf"

                # Use a temp dir for file writing
                temp_dir = tempfile.mkdtemp()
                temp_file_path = os.path.join(temp_dir, file_base_name)
                if document_file:
                    with open(temp_file_path, 'wb+') as destination:
                        for chunk in document_file.chunks():
                            destination.write(chunk)
                else:
                    temp_file_path = None

                # Build the final upload path
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                os.makedirs(full_upload_path, exist_ok=True)

                # Move file from temp to final location
                if document_file:
                    file_path = os.path.join(upload_folder, file_base_name)
                    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    shutil.move(temp_file_path, absolute_file_path)
                else:
                    file_path = None

                # Save the BMCAgreement instance
                bmc = BMCAgreement.objects.create(
                    zone=zone,
                    location=location,
                    contractor=contractor,
                    pan=pan,
                    type_of_agreement=type_of_agreement,
                    agreement_date=agreement_date,
                    start_date=start_date,
                    end_date=end_date,
                    tenure_months=tenure_months,
                    lock_in_period=lock_in_period,
                    monthly_payout=monthly_payout,
                    document_status=document_status,
                    document_pending=document_pending,
                    document=file_path,
                    created_by=request.user if request.user.is_authenticated else None
                )
                print("Saved BMC Agreement:", bmc)

            # Clean up temp dir if still exists
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return HttpResponse("SUBMIT SUCCESSFULLY")
        except Exception as e:
            print("Error saving BMC Agreement:", e)
            # Clean up temp dir and any created folders/files
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if full_upload_path and os.path.exists(full_upload_path):
                try:
                    shutil.rmtree(full_upload_path)
                except Exception:
                    pass
            return HttpResponse(f"Error: {e}", status=500)
    return HttpResponse("Only POST supported for now.")

# A function for merging BMC's incomplete agreement
@csrf_exempt
def bmc_edit_merge(request, pk):
    """
    Merge a new PDF into the existing BMC agreement PDF.
    If the agreement is now expired (based on end_date), move the merged PDF to the Expired folder.
    If the status changes (e.g., INCOMPLETE -> COMPLETE), move the merged PDF to the new status folder and remove the old status folder if empty.
    The folder structure is maintained as:
    Agreements/{Ongoing|Expired}/BMC Agreements/{STATUS}/{Agreement Name}/{STARTDATE}-{ENDDATE}/
    """
    if request.method == "POST":
        print("---- bmc_edit_merge POST ----")
        print("request.POST:", request.POST)
        print("request.FILES:", request.FILES)
        bmc = get_object_or_404(BMCAgreement, pk=pk)
        print(f"Fetched BMCAgreement ID {pk}: {bmc}")

        # Get new values from request
        new_status = request.POST.get("document_status", bmc.document_status)
        print("New status:", new_status)
        new_pending_document = request.POST.get("pending_document", bmc.document_pending)
        print("New pending_document:", new_pending_document)
        new_pdf_file = request.FILES.get("insert_pdf")
        print("New PDF file:", new_pdf_file.name if new_pdf_file else "None")

        if not new_pdf_file:
            print("No PDF uploaded")
            return JsonResponse({"error": "No PDF uploaded"}, status=400)

        temp_dir = None
        full_upload_path = None
        try:
            with transaction.atomic():
                # Verify we have an existing document
                if not bmc.document:
                    print("Error: No existing document to merge with")
                    return JsonResponse({"error": "No existing document to merge with"}, status=400)

                existing_file_path = bmc.document.path
                existing_filename = os.path.basename(bmc.document.name)
                print(f"Existing file path: {existing_file_path}")
                print(f"Existing filename: {existing_filename}")

                # Initialize PDF writer for merged content
                writer = PdfWriter()
                print("Initialized PdfWriter for merging.")

                # Load existing PDF pages
                print("Loading existing PDF...")
                existing_pdf = PdfReader(existing_file_path)
                original_page_count = len(existing_pdf.pages)
                print(f"Existing PDF has {original_page_count} pages")
                
                # Add all existing pages
                for page in existing_pdf.pages:
                    writer.add_page(page)
                print(f"Added {original_page_count} existing pages to writer")

                # Load and add new PDF pages
                print("Loading new PDF to append...")
                new_pdf = PdfReader(new_pdf_file)
                new_page_count = len(new_pdf.pages)
                print(f"New PDF has {new_page_count} pages")
                
                for page in new_pdf.pages:
                    writer.add_page(page)
                print(f"Added {new_page_count} new pages to writer")

                # Write merged content to a temp file
                temp_dir = tempfile.mkdtemp()
                temp_pdf_path = os.path.join(temp_dir, existing_filename)
                with open(temp_pdf_path, 'wb') as temp_f:
                    writer.write(temp_f)
                print(f"Created merged PDF with {len(writer.pages)} total pages at {temp_pdf_path}")

                # Determine if agreement is now expired
                today = date.today()
                end_date_obj = bmc.end_date if isinstance(bmc.end_date, date) else datetime.strptime(str(bmc.end_date), "%Y-%m-%d").date()
                is_expired = end_date_obj and end_date_obj < today

                # Build the correct folder structure
                base_folder = "Expired" if is_expired else "Ongoing"
                agreement_type_folder = "BMC Agreements"
                status_folder = new_status.upper() if new_status else "UNKNOWN"
                agreement_name = os.path.splitext(existing_filename)[0]
                date_folder = f"{bmc.start_date}-{bmc.end_date}"
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                new_file_path = os.path.join(full_upload_path, existing_filename)

                # Only now create the final folder and move the file
                os.makedirs(full_upload_path, exist_ok=True)
                shutil.move(temp_pdf_path, new_file_path)

                # Remove old file if it's in a different location
                if os.path.abspath(existing_file_path) != os.path.abspath(new_file_path):
                    print(f"Moving file from {existing_file_path} to {new_file_path}")
                    if os.path.exists(existing_file_path):
                        os.remove(existing_file_path)
                    # Clean up old empty folders up to status level
                    try:
                        old_date_folder = os.path.dirname(existing_file_path)
                        old_agreement_folder = os.path.dirname(old_date_folder)
                        old_status_folder = os.path.dirname(old_agreement_folder)
                        # Remove date folder if empty
                        if os.path.isdir(old_date_folder) and not os.listdir(old_date_folder):
                            os.rmdir(old_date_folder)
                        # Remove agreement folder if empty
                        if os.path.isdir(old_agreement_folder) and not os.listdir(old_agreement_folder):
                            os.rmdir(old_agreement_folder)
                        # Remove status folder if empty
                        if os.path.isdir(old_status_folder) and not os.listdir(old_status_folder):
                            os.rmdir(old_status_folder)
                    except Exception as cleanup_err:
                        print("Cleanup error:", cleanup_err)

                # Update the document field to the new relative path if location changed
                rel_file_path = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
                if bmc.document.name != rel_file_path.replace("\\", "/"):
                    bmc.document.name = rel_file_path.replace("\\", "/")

                # Update the model to reflect the changes
                bmc.document_status = new_status
                bmc.document_pending = new_pending_document
                bmc.save()

                print("PDF successfully merged and saved with correct folder structure")
                print(f"Final file location: {new_file_path}")
                return JsonResponse({"success": True, "new_page_count": len(writer.pages)})

        except Exception as e:
            print("Exception during PDF merge:", str(e))
            # Clean up temp dir if exists
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            # Optionally, clean up any partially created folders/files in MEDIA_ROOT
            if full_upload_path and os.path.exists(full_upload_path):
                try:
                    shutil.rmtree(full_upload_path)
                except Exception:
                    pass
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            # Always clean up temp dir
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    print("Request method not allowed:", request.method)
    return JsonResponse({"error": "Only POST allowed"}, status=405)


# A function which is used for the searching bmc document by location. 
def bmc_search(request):
    query = request.GET.get('q', '').strip()
    print(f"[bmc_search] Search query: '{query}'")
    if not query:
        print("[bmc_search] No query provided. Returning empty results.")
        return JsonResponse({'results': []})
    results = BMCAgreement.objects.filter(
        location__icontains=query,
        document_status='INCOMPLETE'
    )
    print(f"[bmc_search] Found {results.count()} results for query '{query}'")
    data = []
    for bmc in results:
        doc_url = bmc.document.url if bmc.document else ""
        doc_name = bmc.document.name if bmc.document else ""
        doc_name_only = os.path.basename(doc_name) if doc_name else ""
        print(f"[bmc_search] BMC ID: {bmc.pk}, document.name: '{doc_name}', document.url: '{doc_url}', file name only: '{doc_name_only}'")
        data.append({
            "id": bmc.pk,
            "zone": bmc.zone,
            "location": bmc.location,
            "contractor": bmc.contractor,
            "document_status": bmc.document_status,
            "pending_document": bmc.document_pending,
            "document_url": doc_url,
            "document_name": doc_name_only,
        })
    print(f"[bmc_search] Final data sent: {data}")
    return JsonResponse({'results': data})

# A function for getting bmc document for user who is the viewer. 
@xframe_options_exempt
def bmc_search_viewer(request):
    location = request.GET.get('location', '').strip()
    status = request.GET.get('status', '').strip().upper()
    if not location or not status:
        return JsonResponse({'results': []})

    if status not in ['COMPLETE', 'INCOMPLETE']:
        return JsonResponse({'results': []})

    results = BMCAgreement.objects.filter(
        location__icontains=location,
        document_status=status
    )
    data = []
    for bmc in results:
        start = bmc.start_date
        end = bmc.end_date
        expire_months = months_between_today_and_end(end)
        # Get creator's name or email
        if bmc.created_by:
            creator = f"{bmc.created_by.first_name or ''} {bmc.created_by.last_name or ''}".strip()
            if not creator:
                creator = bmc.created_by.email
        else:
            creator = ""
        data.append({
            "id": bmc.pk,
            "zone": bmc.zone,
            "location": bmc.location,
            "contractor": bmc.contractor,
            "document_status": bmc.document_status,
            "pending_document": bmc.document_pending,
            "document_url": bmc.document.url if bmc.document else "",
            "document_name": bmc.document.name.split('/')[-1] if bmc.document else "",
            "start_date": str(start),
            "end_date": str(end),
            "expire_months": expire_months,
            "created_by": creator,
        })
    return JsonResponse({'results': data})


# A function which is displaying the number of agreements which are either TOTAL, INCOMPLETE, INCOMPLETE
def bmc_stats(request):
    total = BMCAgreement.objects.count()
    complete = BMCAgreement.objects.filter(document_status='COMPLETE').count()
    incomplete = BMCAgreement.objects.filter(document_status='INCOMPLETE').count()
    return JsonResponse({
        "total":total, 
        "complete": complete, 
        "incomplete": incomplete
    })
# ------------------ALL FUNCTION FOR BMC AGREEMENT ENDS HERE----------------

def input_services_create(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Get all required fields from POST
                product = request.POST.get("product")
                contractor = request.POST.get("contractor")
                pan = request.POST.get("pan")
                type_of_agreement = request.POST.get("type_of_agreement")
                agreement_date = request.POST.get("agreement_date")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")
                tenure_months = request.POST.get("tenure_months")
                lock_in_period = request.POST.get("lock_in_period")
                monthly_payout = request.POST.get("monthly_payout")
                document_status = request.POST.get("document_status")
                document_pending = request.POST.get("document_pending")
                document_file = request.FILES.get("document")

                # Parse dates
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

                # Determine if agreement is expired
                today = date.today()
                is_expired = end_date_obj and end_date_obj < today

                # Set base folder: "Ongoing" or "Expired"
                base_folder = "Expired" if is_expired else "Ongoing"

                # Agreement type folder
                agreement_type_folder = "Input Services Agreements"

                # Use status as a folder (COMPLETE/INCOMPLETE/EXPIRED)
                status_folder = document_status.upper() if document_status else "UNKNOWN"

                # Agreement name from product (or file name if you prefer)
                agreement_name = product.strip() if product else (os.path.splitext(document_file.name)[0] if document_file else "UnknownAgreement")

                # Date folder
                date_folder = f"{start_date}-{end_date}"

                # File name (use product as file name if possible)
                file_base_name = f"{agreement_name}.pdf" if document_file else "document.pdf"

                # Build the full path: Agreements/Ongoing/Input Services Agreements/STATUS/AGREEMENT_NAME/STARTDATE-ENDDATE/AGREEMENT_NAME.pdf
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )

                # Ensure the folder exists in MEDIA_ROOT
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                os.makedirs(full_upload_path, exist_ok=True)

                # Save the file to the correct location
                if document_file:
                    file_path = os.path.join(upload_folder, file_base_name)
                    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    with open(absolute_file_path, 'wb+') as destination:
                        for chunk in document_file.chunks():
                            destination.write(chunk)
                else:
                    file_path = None

                # Save the InputServicesAgreement instance
                input_services = InputServicesAgreement.objects.create(
                    product=product,
                    contractor=contractor,
                    pan=pan,
                    type_of_agreement=type_of_agreement,
                    agreement_date=agreement_date,
                    start_date=start_date,
                    end_date=end_date,
                    tenure_months=tenure_months,
                    lock_in_period=lock_in_period,
                    monthly_payout=monthly_payout,
                    document_status=document_status,
                    document_pending=document_pending,
                    document=file_path,  # Save relative path to the file
                    created_by=request.user if request.user.is_authenticated else None
                )
                print("Saved Input Services Agreement:", input_services)

            return HttpResponse("SUBMIT SUCCESSFULLY")
        except Exception as e:
            print("Error saving Input Services Agreement:", e)
            return HttpResponse(f"Error: {e}", status=500)
    return HttpResponse("Only POST supported for now.")



# A function for merging the incomplete input services agreements

@csrf_exempt
def input_services_edit_merge(request, pk):
    """
    Merge a new PDF into the existing Input Services Agreement PDF.
    If the agreement is now expired (based on end_date), move the merged PDF to the Expired folder.
    If the status changes (e.g., INCOMPLETE -> COMPLETE), move the merged PDF to the new status folder and remove the old status folder if empty.
    The folder structure is maintained as:
    Agreements/{Ongoing|Expired}/Input Services Agreements/{STATUS}/{Agreement Name}/{STARTDATE}-{ENDDATE}/
    """
    if request.method == "POST":
        input_services = get_object_or_404(InputServicesAgreement, pk=pk)
        new_status = request.POST.get("document_status", input_services.document_status)
        new_pending_document = request.POST.get("pending_document", input_services.document_pending)
        new_pdf_file = request.FILES.get("insert_pdf")

        if not new_pdf_file:
            return JsonResponse({"error": "No PDF uploaded"}, status=400)

        temp_dir = None
        try:
            with transaction.atomic():
                # Verify we have an existing document
                if not input_services.document:
                    return JsonResponse({"error": "No existing document to merge with"}, status=400)

                existing_file_path = input_services.document.path
                existing_filename = os.path.basename(input_services.document.name)

                # Initialize PDF writer for merged content
                writer = PdfWriter()

                # Load existing PDF pages
                existing_pdf = PdfReader(existing_file_path)
                for page in existing_pdf.pages:
                    writer.add_page(page)

                # Load and add new PDF pages
                new_pdf = PdfReader(new_pdf_file)
                for page in new_pdf.pages:
                    writer.add_page(page)

                # Write merged content to a temp file
                temp_dir = tempfile.mkdtemp()
                temp_pdf_path = os.path.join(temp_dir, existing_filename)
                with open(temp_pdf_path, 'wb') as temp_f:
                    writer.write(temp_f)

                # Determine if agreement is now expired
                today = date.today()
                end_date_obj = input_services.end_date if isinstance(input_services.end_date, date) else datetime.strptime(str(input_services.end_date), "%Y-%m-%d").date()
                is_expired = end_date_obj and end_date_obj < today

                # Build the correct folder structure
                base_folder = "Expired" if is_expired else "Ongoing"
                agreement_type_folder = "Input Services Agreements"
                status_folder = new_status.upper() if new_status else "UNKNOWN"
                agreement_name = os.path.splitext(existing_filename)[0]
                date_folder = f"{input_services.start_date}-{input_services.end_date}"
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                new_file_path = os.path.join(full_upload_path, existing_filename)

                # Only now create the final folder and move the file
                os.makedirs(full_upload_path, exist_ok=True)
                shutil.move(temp_pdf_path, new_file_path)

                # Remove old file if it's in a different location
                if os.path.abspath(existing_file_path) != os.path.abspath(new_file_path):
                    if os.path.exists(existing_file_path):
                        os.remove(existing_file_path)
                    # Clean up old empty folders up to status level
                    try:
                        old_date_folder = os.path.dirname(existing_file_path)
                        old_agreement_folder = os.path.dirname(old_date_folder)
                        old_status_folder = os.path.dirname(old_agreement_folder)
                        if os.path.isdir(old_date_folder) and not os.listdir(old_date_folder):
                            os.rmdir(old_date_folder)
                        if os.path.isdir(old_agreement_folder) and not os.listdir(old_agreement_folder):
                            os.rmdir(old_agreement_folder)
                        if os.path.isdir(old_status_folder) and not os.listdir(old_status_folder):
                            os.rmdir(old_status_folder)
                    except Exception:
                        pass

                # Update the document field to the new relative path if location changed
                rel_file_path = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
                if input_services.document.name != rel_file_path.replace("\\", "/"):
                    input_services.document.name = rel_file_path.replace("\\", "/")

                # Update the model to reflect the changes
                input_services.document_status = new_status
                input_services.document_pending = new_pending_document
                input_services.save()

                return JsonResponse({"success": True, "new_page_count": len(writer.pages)})

        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if 'full_upload_path' in locals() and os.path.exists(full_upload_path):
                try:
                    shutil.rmtree(full_upload_path)
                except Exception:
                    pass
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    return JsonResponse({"error": "Only POST allowed"}, status=405)

# A function for searching input services agreement by contractor and product name and this is used for editing purposes. 

import pprint

def input_services_search(request):
    contractor = request.GET.get('contractor', '').strip()
    product = request.GET.get('product', '').strip()
    results = []
    if contractor and product:
        qs = InputServicesAgreement.objects.filter(
            contractor__icontains=contractor,
            product__icontains=product,
            document_status='INCOMPLETE'
        )
        for obj in qs:
            results.append({
                'id': obj.id,
                'contractor': obj.contractor,
                'product': obj.product,
                'document_status': obj.document_status,
                'document_pending': obj.document_pending,
                'document_url': obj.document.url if obj.document else '',
                'document_name': obj.document.name.split('/')[-1] if obj.document else '',
            })
    print("input_services_search GET params:")
    pprint.pprint(dict(request.GET))
    print("input_services_search results:")
    pprint.pprint(results)
    return JsonResponse({'results': results})

# A function for seeing the input services agreement for viewer person.
@xframe_options_exempt
def input_services_search_viewer(request):
    try:
        contractor = request.GET.get('contractor', '').strip()
        product = request.GET.get('product', '').strip()
        status = request.GET.get('status', '').strip().upper()

        print("[input_services_search_viewer] GET params:")
        print("  contractor:", contractor)
        print("  product:", product)
        print("  status:", status)

        qs = InputServicesAgreement.objects.all()
        if status:
            qs = qs.filter(document_status__iexact=status)
        if contractor:
            qs = qs.filter(contractor__icontains=contractor)
        if product:
            qs = qs.filter(product__icontains=product)

        def format_dmy(date_obj):
            if not date_obj:
                return ""
            return date_obj.strftime("%d/%m/%y")

        results = []
        for obj in qs:
            start = obj.start_date
            end = obj.end_date
            expire_months = months_between_today_and_end(end) if end else "-"
            if obj.created_by:
                creator = f"{obj.created_by.first_name or ''} {obj.created_by.last_name or ''}".strip()
                if not creator:
                    creator = obj.created_by.email
            else:
                creator = ""
            results.append({
                "id": obj.id,
                "agreement_date": format_dmy(getattr(obj, "agreement_date", None)),
                "product": getattr(obj, "product", ""),
                "contractor": obj.contractor,
                "document_status": obj.document_status,
                "pending_document": getattr(obj, "document_pending", ""),
                "start_date": format_dmy(start) if start else "",
                "end_date": format_dmy(end) if end else "",
                "expire_months": expire_months,
                "created_by": creator,
                "document_url": obj.document.url if obj.document else "",
            })
        print("[input_services_search_viewer] Results:")
        import pprint
        pprint.pprint(results)
        return JsonResponse({"results": results})
    except Exception as e:
        print(f"[input_services_search_viewer] Exception occurred: {e}")
        return JsonResponse({"error": str(e)}, status=500)

def input_services_stats(request):
    total = InputServicesAgreement.objects.count()
    complete = InputServicesAgreement.objects.filter(document_status='COMPLETE').count()
    incomplete = InputServicesAgreement.objects.filter(document_status='INCOMPLETE').count()
    return JsonResponse({
        "total":total, 
        "complete": complete, 
        "incomplete": incomplete
    })

# --------------------ALL INPUT SERVICE AGREEMENT ENDS HERE---------------------------------

def consultant_create(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Get all required fields from POST
                category = request.POST.get("category")
                contractor = request.POST.get("contractor")
                pan = request.POST.get("pan")
                type_of_agreement = request.POST.get("type_of_agreement")
                agreement_date = request.POST.get("agreement_date")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")
                tenure_months = request.POST.get("tenure_months")
                lock_in_period = request.POST.get("lock_in_period")
                monthly_payout = request.POST.get("monthly_payout")
                document_status = request.POST.get("document_status")
                document_pending = request.POST.get("document_pending")
                document_file = request.FILES.get("document")

                # Parse dates
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

                # Determine if agreement is expired
                today = date.today()
                is_expired = end_date_obj and end_date_obj < today

                # Set base folder: "Ongoing" or "Expired"
                base_folder = "Expired" if is_expired else "Ongoing"

                # Agreement type folder
                agreement_type_folder = "Consultant Agreements"

                # Use status as a folder (COMPLETE/INCOMPLETE/EXPIRE)
                status_folder = document_status.upper() if document_status else "UNKNOWN"

                # Agreement name from category (or file name if you prefer)
                agreement_name = category.strip() if category else (os.path.splitext(document_file.name)[0] if document_file else "UnknownAgreement")

                # Date folder
                date_folder = f"{start_date}-{end_date}"

                # File name (use category as file name if possible)
                file_base_name = f"{agreement_name}.pdf" if document_file else "document.pdf"

                # Build the full path: Agreements/Ongoing/Consultant Agreements/STATUS/AGREEMENT_NAME/STARTDATE-ENDDATE/AGREEMENT_NAME.pdf
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )

                # Ensure the folder exists in MEDIA_ROOT
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                os.makedirs(full_upload_path, exist_ok=True)

                # Save the file to the correct location
                if document_file:
                    file_path = os.path.join(upload_folder, file_base_name)
                    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    with open(absolute_file_path, 'wb+') as destination:
                        for chunk in document_file.chunks():
                            destination.write(chunk)
                else:
                    file_path = None

                # Save the ConsultantAgreement instance
                consultant_agreement = ConsultantAgreement.objects.create(
                    category=category,
                    contractor=contractor,
                    pan=pan,
                    type_of_agreement=type_of_agreement,
                    agreement_date=agreement_date,
                    start_date=start_date,
                    end_date=end_date,
                    tenure_months=tenure_months,
                    lock_in_period=lock_in_period,
                    monthly_payout=monthly_payout,
                    document_status=document_status,
                    document_pending=document_pending,
                    document=file_path,  # Save relative path to the file
                    created_by=request.user if request.user.is_authenticated else None
                )
                print("Saved Consultant Agreement:", consultant_agreement)

            return HttpResponse("SUBMIT SUCCESSFULLY")
        except Exception as e:
            print("Error saving Consultant Agreement:", e)
            return HttpResponse(f"Error: {e}", status=500)
    return HttpResponse("Only POST supported for now.")



def consultant_search(request):
    category = request.GET.get('category', '').strip()
    print("The category is ", category)
    contractor = request.GET.get('contractor', '').strip()
    print("The contractor is ", contractor)
    print("consultant_search GET params:", {"category": category, "contractor": contractor})
    qs = ConsultantAgreement.objects.filter(category__icontains=category, contractor__icontains=contractor)
    print("The query string is", qs)
    results = []
    for obj in qs:
        if obj.document and obj.document.path:
            try:
                reader = PdfReader(obj.document.path)
                page_count = len(reader.pages)
                print(f"ConsultantAgreement ID {obj.id} document has {page_count} pages")
            except Exception as e:
                print(f"Error reading PDF for ConsultantAgreement ID {obj.id}: {e}")
        results.append({
            "id": obj.id,
            "category": obj.category,
            "contractor": obj.contractor,
            "document_status": obj.document_status,
            "document_pending": obj.document_pending,
            "document_url": obj.document.url if obj.document else "",
            "document_name": obj.document.name.split('/')[-1] if obj.document else "",
        })
    print("consultant_search results:", results)
    return JsonResponse({"results": results})


@csrf_exempt
def consultant_edit_merge(request, pk):
    """
    Merge a new PDF into the existing Consultant Agreement PDF.
    If the agreement is now expired (based on end_date), move the merged PDF to the Expired folder.
    If the status changes (e.g., INCOMPLETE -> COMPLETE), move the merged PDF to the new status folder and remove the old status folder if empty.
    The folder structure is maintained as:
    Agreements/{Ongoing|Expired}/Consultant Agreements/{STATUS}/{Agreement Name}/{STARTDATE}-{ENDDATE}/
    """
    if request.method == "POST":
        print("---- consultant_edit_merge POST ----")
        print("request.POST:", dict(request.POST))
        print("request.FILES:", request.FILES)
        consultant = get_object_or_404(ConsultantAgreement, pk=pk)
        print(f"Fetched ConsultantAgreement ID {pk}: {consultant}")

        new_status = request.POST.get("document_status", consultant.document_status)
        print("New status:", new_status)
        new_pending_document = request.POST.get("pending_document", consultant.document_pending)
        print("New pending_document:", new_pending_document)
        new_pdf_file = request.FILES.get("insert_pdf")
        print("New PDF file:", new_pdf_file.name if new_pdf_file else "None")

        if not new_pdf_file:
            print("No PDF uploaded")
            return JsonResponse({"error": "No PDF uploaded"}, status=400)

        temp_dir = None
        try:
            with transaction.atomic():
                # Verify we have an existing document
                if not consultant.document:
                    print("Error: No existing document to merge with")
                    return JsonResponse({"error": "No existing document to merge with"}, status=400)

                existing_file_path = consultant.document.path
                existing_filename = os.path.basename(consultant.document.name)
                print(f"Existing file path: {existing_file_path}")
                print(f"Existing filename: {existing_filename}")

                # Initialize PDF writer for merged content
                writer = PdfWriter()
                print("Initialized PdfWriter for merging.")

                # Load existing PDF pages
                print("Loading existing PDF...")
                existing_pdf = PdfReader(existing_file_path)
                original_page_count = len(existing_pdf.pages)
                print(f"Existing PDF has {original_page_count} pages")
                for page in existing_pdf.pages:
                    writer.add_page(page)
                print(f"Added {original_page_count} existing pages to writer")

                # Load and add new PDF pages
                print("Loading new PDF to append...")
                new_pdf = PdfReader(new_pdf_file)
                new_page_count = len(new_pdf.pages)
                print(f"New PDF has {new_page_count} pages")
                for page in new_pdf.pages:
                    writer.add_page(page)
                print(f"Added {new_page_count} new pages to writer")

                # Write merged content to a temp file
                temp_dir = tempfile.mkdtemp()
                temp_pdf_path = os.path.join(temp_dir, existing_filename)
                with open(temp_pdf_path, 'wb') as temp_f:
                    writer.write(temp_f)
                print(f"Created merged PDF with {len(writer.pages)} total pages at {temp_pdf_path}")

                # Determine if agreement is now expired
                today = date.today()
                end_date_obj = consultant.end_date if isinstance(consultant.end_date, date) else datetime.strptime(str(consultant.end_date), "%Y-%m-%d").date()
                is_expired = end_date_obj and end_date_obj < today
                print(f"Agreement expired? {is_expired} (end_date: {consultant.end_date}, today: {today})")

                # Build the correct folder structure
                base_folder = "Expired" if is_expired else "Ongoing"
                agreement_type_folder = "Consultant Agreements"
                status_folder = new_status.upper() if new_status else "UNKNOWN"
                agreement_name = os.path.splitext(existing_filename)[0]
                date_folder = f"{consultant.start_date}-{consultant.end_date}"
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                new_file_path = os.path.join(full_upload_path, existing_filename)
                print(f"Final upload folder: {upload_folder}")
                print(f"Full upload path: {full_upload_path}")
                print(f"New file path: {new_file_path}")

                # Only now create the final folder and move the file
                os.makedirs(full_upload_path, exist_ok=True)
                shutil.move(temp_pdf_path, new_file_path)
                print(f"Moved merged PDF to {new_file_path}")

                # Remove old file if it's in a different location
                if os.path.abspath(existing_file_path) != os.path.abspath(new_file_path):
                    print(f"Moving file from {existing_file_path} to {new_file_path}")
                    if os.path.exists(existing_file_path):
                        os.remove(existing_file_path)
                    # Clean up old empty folders up to status level
                    try:
                        old_date_folder = os.path.dirname(existing_file_path)
                        old_agreement_folder = os.path.dirname(old_date_folder)
                        old_status_folder = os.path.dirname(old_agreement_folder)
                        if os.path.isdir(old_date_folder) and not os.listdir(old_date_folder):
                            os.rmdir(old_date_folder)
                        if os.path.isdir(old_agreement_folder) and not os.listdir(old_agreement_folder):
                            os.rmdir(old_agreement_folder)
                        if os.path.isdir(old_status_folder) and not os.listdir(old_status_folder):
                            os.rmdir(old_status_folder)
                        print("Cleaned up old empty folders if needed.")
                    except Exception as cleanup_err:
                        print("Cleanup error:", cleanup_err)

                # Update the document field to the new relative path if location changed
                rel_file_path = os.path.relpath(new_file_path, settings.MEDIA_ROOT)
                if consultant.document.name != rel_file_path.replace("\\", "/"):
                    consultant.document.name = rel_file_path.replace("\\", "/")
                    print(f"Updated consultant.document.name to {consultant.document.name}")

                # Update the model to reflect the changes
                consultant.document_status = new_status
                consultant.document_pending = new_pending_document
                consultant.save()
                print("PDF successfully merged and saved with correct folder structure")
                print(f"Final file location: {new_file_path}")

                return JsonResponse({"success": True, "new_page_count": len(writer.pages)})

        except Exception as e:
            print("Exception during PDF merge:", str(e))
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if 'full_upload_path' in locals() and os.path.exists(full_upload_path):
                try:
                    shutil.rmtree(full_upload_path)
                except Exception:
                    pass
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    print("Request method not allowed:", request.method)
    return JsonResponse({"error": "Only POST allowed"}, status=405)


@xframe_options_exempt
def consultant_search_viewer(request):
    try:
        category = request.GET.get('category', '').strip().upper()
        contractor = request.GET.get('contractor', '').strip()
        status = request.GET.get('status', '').strip().upper()

        print("[consultant_search_viewer] GET params:")
        print("  category:", category)
        print("  contractor:", contractor)
        print("  status:", status)

        qs = ConsultantAgreement.objects.all()
        if category:
            qs = qs.filter(category__iexact=category)
        if contractor:
            qs = qs.filter(contractor__icontains=contractor)
        if status:
            qs = qs.filter(document_status__iexact=status)

        def format_dmy(date_obj):
            if not date_obj:
                return ""
            return date_obj.strftime("%d/%m/%y")

        results = []
        for obj in qs:
            start = obj.start_date
            end = obj.end_date
            expire_months = months_between_today_and_end(end) if end else "-"
            if obj.created_by:
                creator = f"{obj.created_by.first_name or ''} {obj.created_by.last_name or ''}".strip()
                if not creator:
                    creator = obj.created_by.email
            else:
                creator = ""
            results.append({
                "id": obj.id,
                "agreement_date": format_dmy(getattr(obj, "agreement_date", None)),
                "category": getattr(obj, "category", ""),
                "contractor": obj.contractor,
                "document_status": obj.document_status,
                "pending_document": getattr(obj, "document_pending", ""),
                "start_date": format_dmy(start) if start else "",
                "end_date": format_dmy(end) if end else "",
                "expire_months": expire_months,
                "created_by": creator,
                "document_url": obj.document.url if obj.document else "",
            })
        print("[consultant_search_viewer] Results:")
        import pprint
        pprint.pprint(results)
        return JsonResponse({"results": results})
    except Exception as e:
        print(f"[consultant_search_viewer] Exception occurred: {e}")
        return JsonResponse({"error": str(e)}, status=500)

# ----------------ALL CONSULTANT AGREEMENT ENDS HERE---------------------


def cook_create(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                # Get all required fields from POST
                zone = request.POST.get("zone")
                location = request.POST.get("location")
                contractor = request.POST.get("contractor")
                pan = request.POST.get("pan")
                type_of_agreement = request.POST.get("type_of_agreement")
                agreement_date = request.POST.get("agreement_date")
                start_date = request.POST.get("start_date")
                end_date = request.POST.get("end_date")
                tenure_months = request.POST.get("tenure_months")
                lock_in_period = request.POST.get("lock_in_period")
                monthly_payout = request.POST.get("monthly_payout")
                document_status = request.POST.get("document_status")
                document_pending = request.POST.get("document_pending")
                document_file = request.FILES.get("document")

                # Parse dates
                agreement_date_obj = datetime.strptime(agreement_date, "%Y-%m-%d").date() if agreement_date else None
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else None
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None

                # Determine if agreement is expired
                today = date.today()
                is_expired = end_date_obj and end_date_obj < today

                # Set base folder: "Ongoing" or "Expired"
                base_folder = "Expired" if is_expired else "Ongoing"

                # Agreement type folder
                agreement_type_folder = "Cook Agreements"

                # Use status as a folder (COMPLETE/INCOMPLETE/EXPIRE)
                status_folder = document_status.upper() if document_status else "UNKNOWN"

                # Agreement name from contractor (or file name if you prefer)
                agreement_name = contractor.strip() if contractor else (os.path.splitext(document_file.name)[0] if document_file else "UnknownAgreement")

                # Date folder
                date_folder = f"{start_date}-{end_date}"

                # File name (use contractor as file name if possible)
                file_base_name = f"{agreement_name}.pdf" if document_file else "document.pdf"

                # Build the full path: Agreements/Ongoing/Cook Agreements/STATUS/AGREEMENT_NAME/STARTDATE-ENDDATE/AGREEMENT_NAME.pdf
                upload_folder = os.path.join(
                    "Agreements",
                    base_folder,
                    agreement_type_folder,
                    status_folder,
                    agreement_name,
                    date_folder
                )

                # Ensure the folder exists in MEDIA_ROOT
                full_upload_path = os.path.join(settings.MEDIA_ROOT, upload_folder)
                os.makedirs(full_upload_path, exist_ok=True)

                # Save the file to the correct location
                if document_file:
                    file_path = os.path.join(upload_folder, file_base_name)
                    absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    with open(absolute_file_path, 'wb+') as destination:
                        for chunk in document_file.chunks():
                            destination.write(chunk)
                else:
                    file_path = None

                # Save the CookAgreement instance
                cook_agreement = CookAgreement.objects.create(
                    zone=zone,
                    location=location,
                    contractor=contractor,
                    pan=pan,
                    type_of_agreement=type_of_agreement,
                    agreement_date=agreement_date_obj,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    tenure_months=tenure_months,
                    lock_in_period=lock_in_period,
                    monthly_payout=monthly_payout,
                    document_status=document_status,
                    document_pending=document_pending,
                    document=file_path,  # Save relative path to the file
                    created_by=request.user if request.user.is_authenticated else None
                )
                print("Saved Cook Agreement:", cook_agreement)

            return HttpResponse("SUBMIT SUCCESSFULLY")
        except Exception as e:
            print("Error saving Cook Agreement:", e)
            return HttpResponse(f"Error: {e}", status=500)
    return HttpResponse("Only POST supported for now.")

def cook_search(request):
    location = request.GET.get('location', '').strip()
    print("The location is ", location)
    contractor = request.GET.get('contractor', '').strip()
    print("The contractor is ", contractor)
    print("cook_search GET params:", {"location": location, "contractor": contractor})
    qs = CookAgreement.objects.filter(location__icontains=location, contractor__icontains=contractor)
    print("The query string is", qs)
    results = []
    for obj in qs:
        if obj.document and obj.document.path:
            try:
                reader = PdfReader(obj.document.path)
                page_count = len(reader.pages)
                print(f"CookAgreement ID {obj.id} document has {page_count} pages")
            except Exception as e:
                print(f"Error reading PDF for CookAgreement ID {obj.id}: {e}")
        results.append({
            "id": obj.id,
            "zone": obj.zone,
            "location": obj.location,
            "contractor": obj.contractor,
            "document_status": obj.document_status,
            "document_pending": obj.document_pending,
            "document_url": obj.document.url if obj.document else "",
            "document_name": obj.document.name.split('/')[-1] if obj.document else "",
        })
    print("cook_search results:", results)
    return JsonResponse({"results": results})

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        print(f"Login attempt: email={email}, password={password}")
        user = authenticate(request, username=email, password=password)
        print(f"Authenticate returned: {user}")
        if user is not None:
            print(f"User role: {user.role}")
        if user is not None and user.role == "viewer":
            print("Login successful, redirecting to viewer page.")
            auth_login(request, user)
            return redirect('viewer')
        if user is not None and user.role == "data_entry":
            print("Login successful, redirecting to data entry page.")
            auth_login(request, user)
            return redirect('data-entry')
        if user is not None and user.role == "approver":
            print("Login successful, redirecting to approver page.")
        else:
            print("Login failed: Invalid credentials or not a viewer.")
            return render(request, 'login.html', {"error": "Invalid credentials or not a viewer."})
    return render(request, 'login.html')

def logout_view(request):
    print(request)
    logout(request)
    print(logout(request))
    return redirect('login')

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@login_required
def viewer_page(request):
    if not hasattr(request.user, "role") or request.user.role != "viewer":
        return render(request, "403_fallback.html", {"message": "You are not authorized to visit this page"}, status=403)
    return render(request, 'viewer_page.html')

@login_required
def data_entry_page(request):
    if not hasattr(request.user, "role") or request.user.role != "data_entry":
        return render(request, "403_fallback.html", {"message": "You are not authorized to visit this page"}, status=403)
    total_incomplete = BMCAgreement.objects.filter(document_status='INCOMPLETE').count()
    total_complete = BMCAgreement.objects.filter(document_status='COMPLETE').count()
    return render(request, 'data_entry_page.html', {
        'user': request.user,
        'total_incomplete': total_incomplete,
        'total_complete': total_complete,
    })

# Optional: Custom 404 handler for URL mismatch
def custom_404_view(request, exception=None):
    return render(request, "403_fallback.html", {"message": "Please don't modify the url"}, status=404)