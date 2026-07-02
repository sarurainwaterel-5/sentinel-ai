from app.services.fingerprint_service import FingerprintService

hash_value = FingerprintService.calculate_sha256(
    "backend/uploads/YOUR_PDF_NAME.pdf"
)

print(hash_value)
