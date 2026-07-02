import hashlib


class FingerprintService:

    @staticmethod
    def calculate_sha256(file_path: str):

        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:

            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()
