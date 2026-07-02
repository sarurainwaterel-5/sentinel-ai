import hashlib


class FingerprintService:
    @staticmethod
    def calculate_sha256(file_path: str) -> str:
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as file:
            while True:
                chunk = file.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)

        return sha256.hexdigest()
