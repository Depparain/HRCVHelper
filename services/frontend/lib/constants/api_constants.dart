class ApiConstants {
  // Базовый URL API Gateway (по умолчанию localhost:8000)
  static String baseUrl = 'http://localhost:8000';

  // Эндпоинты авторизации
  static String get loginUrl => '$baseUrl/api/v1/auth/login';

  // Эндпоинты резюме (CV)
  static String get cvUploadUrl => '$baseUrl/api/v1/cv/upload';
  static String cvValidateUrl(int cvId) => '$baseUrl/api/v1/cv/$cvId/validate';
  static String cvDetailUrl(int cvId) => '$baseUrl/api/v1/cv/$cvId';
  static String cvDownloadUrl(int cvId) => '$baseUrl/api/v1/cv/$cvId/download';
  static String get cvListUrl => '$baseUrl/api/v1/cv';

  // Эндпоинты администратора
  static String get adminLogsUrl => '$baseUrl/api/v1/admin/logs';
  static String get adminHealthUrl => '$baseUrl/api/v1/admin/health';
}
