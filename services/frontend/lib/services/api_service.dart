import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../constants/api_constants.dart';
import '../models/user_model.dart';
import '../models/cv_model.dart';
import '../models/log_model.dart';

class ApiService {
  String? _authToken;

  void setToken(String? token) {
    _authToken = token;
  }

  Map<String, String> get _headers {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  // --- Авторизация HR ---

  Future<LoginResponse> login(String login, String password) async {
    final response = await http.post(
      Uri.parse(ApiConstants.loginUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'login': login, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final loginResp = LoginResponse.fromJson(data);
      setToken(loginResp.accessToken);
      return loginResp;
    } else {
      String errorMsg = 'Ошибка авторизации';
      try {
        final errData = jsonDecode(utf8.decode(response.bodyBytes));
        errorMsg = errData['detail'] ?? errorMsg;
      } catch (_) {}
      throw Exception(errorMsg);
    }
  }

  // --- Загрузка и парсинг CV ---

  Future<CVRecord> uploadCV(Uint8List fileBytes, String filename, int hrId) async {
    final request = http.MultipartRequest('POST', Uri.parse(ApiConstants.cvUploadUrl));
    if (_authToken != null) {
      request.headers['Authorization'] = 'Bearer $_authToken';
    }

    request.fields['hr_id'] = hrId.toString();
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        fileBytes,
        filename: filename,
      ),
    );

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return CVRecord.fromJson(data);
    } else {
      String errorMsg = 'Ошибка при загрузке резюме';
      try {
        final errData = jsonDecode(utf8.decode(response.bodyBytes));
        errorMsg = errData['detail'] ?? errorMsg;
      } catch (_) {}
      throw Exception(errorMsg);
    }
  }

  // --- Валидация JSON и генерация DOCX ---

  Future<CVRecord> validateCV(int cvId, CVJsonData updatedJson) async {
    final response = await http.put(
      Uri.parse(ApiConstants.cvValidateUrl(cvId)),
      headers: _headers,
      body: jsonEncode(updatedJson.toJson()),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return CVRecord.fromJson(data);
    } else {
      String errorMsg = 'Ошибка сохранения и генерации DOCX';
      try {
        final errData = jsonDecode(utf8.decode(response.bodyBytes));
        errorMsg = errData['detail'] ?? errorMsg;
      } catch (_) {}
      throw Exception(errorMsg);
    }
  }

  // --- Получение данных резюме ---

  Future<CVRecord> getCV(int cvId) async {
    final response = await http.get(
      Uri.parse(ApiConstants.cvDetailUrl(cvId)),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return CVRecord.fromJson(data);
    } else {
      throw Exception('Не удалось загрузить данные резюме $cvId');
    }
  }

  // --- Список резюме ---

  Future<List<CVRecord>> listCVs({int? hrId}) async {
    String url = ApiConstants.cvListUrl;
    if (hrId != null) {
      url += '?hr_id=$hrId';
    }

    final response = await http.get(
      Uri.parse(url),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = jsonDecode(utf8.decode(response.bodyBytes));
      return data.map((e) => CVRecord.fromJson(e as Map<String, dynamic>)).toList();
    } else {
      throw Exception('Ошибка загрузки списка резюме');
    }
  }

  // --- Скачивание DOCX файла ---

  Future<Uint8List> downloadDocxBytes(int cvId) async {
    final response = await http.get(
      Uri.parse(ApiConstants.cvDownloadUrl(cvId)),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      return response.bodyBytes;
    } else {
      throw Exception('Не удалось скачать файл .docx');
    }
  }

  // --- Системные логи (Админ) ---

  Future<List<LogItem>> getLogs({int limit = 100}) async {
    final response = await http.get(
      Uri.parse('${ApiConstants.adminLogsUrl}?limit=$limit'),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      final List<dynamic> logs = data['logs'] ?? [];
      return logs.map((e) => LogItem.fromJson(e as Map<String, dynamic>)).toList();
    } else {
      throw Exception('Ошибка загрузки логов');
    }
  }

  // --- Мониторинг работоспособности (Health report) ---

  Future<HealthReport> getHealth() async {
    final response = await http.get(
      Uri.parse(ApiConstants.adminHealthUrl),
      headers: _headers,
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      return HealthReport.fromJson(data);
    } else {
      throw Exception('Ошибка получения отчета работоспособности');
    }
  }
}

final apiService = ApiService();
