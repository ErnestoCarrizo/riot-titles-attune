class AppError(Exception):
    def __init__(self, message: str, status_code: int, *, retry_after: str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.retry_after = retry_after


class ConfigurationError(AppError):
    def __init__(self):
        super().__init__("La API de Riot no está configurada en el servidor.", 503)


class ExternalSchemaError(AppError):
    def __init__(self, source: str):
        super().__init__(f"La respuesta de {source} tiene un formato inesperado.", 502)


class CatalogUnavailableError(AppError):
    def __init__(self):
        super().__init__("No se pudo cargar el catálogo de títulos en este momento.", 502)


class AccountNotFoundError(AppError):
    def __init__(self):
        super().__init__("No encontramos una cuenta con ese Riot ID.", 404)


class TitleNotFoundError(AppError):
    def __init__(self):
        super().__init__("No encontramos ese título en el catálogo actual.", 404)


class RiotRateLimitError(AppError):
    def __init__(self, retry_after: str | None = None):
        super().__init__("Riot indicó que se alcanzó el límite de consultas.", 429, retry_after=retry_after)


class RiotUnavailableError(AppError):
    def __init__(self):
        super().__init__("Riot no está disponible o rechazó la credencial del servidor.", 502)


class ExternalTimeoutError(AppError):
    def __init__(self):
        super().__init__("La consulta externa tardó demasiado en responder.", 504)
