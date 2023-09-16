import unicodedata


class NormalizeValidators:
    """Нормализуем введённые данные"""
    
    @classmethod
    def normalize_email(cls, email: str) -> str:
        """Возвращаем адресс приведенный к нижнему регистру"""
        email = email or ""
        try:
            email_name, domain_part = email.strip().rsplit("@", 1)
        except ValueError:
            pass
        else:
            email = email_name.lower() + "@" + domain_part.lower()
        return email

    @classmethod
    def normalize_username(cls, username: str) -> str:
        """Возвращаем нормализованный юзернэйм и делаем первую букву заглавной"""
        return unicodedata.normalize("NFKC", username).capitalize()

    @staticmethod
    def _normalize_human_names(name: str) -> str:
        """Нормализуем имена и фамилии"""
        name = name.strip().lower()
        return " ".join(word.capitalize() for word in name.split())

    def clean(self) -> None:
        self.first_name = self._normalize_human_names(self.first_name)
        self.last_name = self._normalize_human_names(self.last_name)
        return super().clean()