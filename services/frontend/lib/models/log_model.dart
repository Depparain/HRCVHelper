class LogItem {
  final String timestamp;
  final String level;
  final String service;
  final String message;

  LogItem({
    required this.timestamp,
    required this.level,
    required this.service,
    required this.message,
  });

  factory LogItem.fromJson(Map<String, dynamic> json) {
    return LogItem(
      timestamp: json['timestamp'] ?? '',
      level: json['level'] ?? 'INFO',
      service: json['service'] ?? 'unknown',
      message: json['message'] ?? '',
    );
  }
}

class ServiceStatus {
  final String service;
  final String status;
  final Map<String, dynamic>? details;

  ServiceStatus({
    required this.service,
    required this.status,
    this.details,
  });

  factory ServiceStatus.fromJson(Map<String, dynamic> json) {
    return ServiceStatus(
      service: json['service'] ?? '',
      status: json['status'] ?? 'unknown',
      details: json['details'] as Map<String, dynamic>?,
    );
  }

  bool get isHealthy => status == 'healthy' || status == 'ok';
}

class HealthReport {
  final String status;
  final String timestamp;
  final Map<String, ServiceStatus> services;

  HealthReport({
    required this.status,
    required this.timestamp,
    required this.services,
  });

  factory HealthReport.fromJson(Map<String, dynamic> json) {
    final rawServices = (json['services'] as Map<String, dynamic>?) ?? {};
    final mappedServices = rawServices.map(
      (k, v) => MapEntry(k, ServiceStatus.fromJson(v as Map<String, dynamic>)),
    );

    return HealthReport(
      status: json['status'] ?? 'unknown',
      timestamp: json['timestamp'] ?? '',
      services: mappedServices,
    );
  }

  bool get isHealthy => status == 'healthy' || status == 'ok';
}
