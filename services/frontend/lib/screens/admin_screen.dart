import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_theme.dart';
import '../models/log_model.dart';
import '../services/api_service.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  HealthReport? _healthReport;
  List<LogItem> _logs = [];
  bool _isLoading = true;
  String _selectedLevel = 'ALL';
  String _logSearchQuery = '';
  Timer? _refreshTimer;
  bool _autoRefresh = true;
  String _lastSyncedTime = 'Только что';

  @override
  void initState() {
    super.initState();
    _loadData();
    _refreshTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (_autoRefresh && mounted) {
        _loadData(silent: true);
      }
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData({bool silent = false}) async {
    if (!silent) setState(() => _isLoading = true);

    try {
      final health = await apiService.getHealth();
      final logs = await apiService.getLogs(limit: 200);

      final now = DateTime.now();
      final timeStr =
          '${now.hour.toString().padLeft(2, '0')}:${now.minute.toString().padLeft(2, '0')}:${now.second.toString().padLeft(2, '0')}';

      if (mounted) {
        setState(() {
          _healthReport = health;
          _logs = logs;
          _isLoading = false;
          _lastSyncedTime = timeStr;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  List<LogItem> get _filteredLogs {
    return _logs.where((l) {
      if (_selectedLevel != 'ALL' && l.level.toUpperCase() != _selectedLevel) {
        return false;
      }
      if (_logSearchQuery.isNotEmpty) {
        final q = _logSearchQuery.toLowerCase();
        return l.message.toLowerCase().contains(q) ||
            l.service.toLowerCase().contains(q);
      }
      return true;
    }).toList();
  }

  void _copyAllLogs() {
    final buffer = StringBuffer();
    for (final l in _filteredLogs) {
      buffer.writeln('${l.timestamp} [${l.level}] [${l.service}]: ${l.message}');
    }
    Clipboard.setData(ClipboardData(text: buffer.toString()));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Логи скопированы в буфер обмена')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
        title: Row(
          children: [
            const Icon(Icons.dns_rounded, color: AppColors.secondary),
            const SizedBox(width: 8),
            const Text('HRCVHelper'),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainer,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text('Контур Администратора', style: TextStyle(fontSize: 11, color: AppColors.secondary)),
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
        child: Center(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 1440),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Top Header & Telemetry Bar
                _buildTelemetryHeader(),
                const SizedBox(height: 20),

                // Controls Bar (Auto-refresh, Level filter, Refresh button)
                _buildControlsBar(),
                const SizedBox(height: 24),

                // Section 1: Microservices Health Report Grid
                _buildHealthSection(),
                const SizedBox(height: 28),

                // Section 2: Real-time System Logs
                _buildLogsSection(),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTelemetryHeader() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 6,
                  height: 6,
                  decoration: const BoxDecoration(
                    color: AppColors.secondary,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                const Text(
                  'МОНИТОРИНГ КЛАСТЕРА v2.4',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.8, color: AppColors.secondary),
                ),
                const SizedBox(width: 6),
                const Text('• Режим супервайзера', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Панель технического мониторинга и системных логов',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
                fontFamily: 'Plus Jakarta Sans',
                letterSpacing: -0.4,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Диагностика микросервисов, метрик очередей и логов в реальном времени',
              style: TextStyle(fontSize: 13, color: AppColors.textMuted),
            ),
          ],
        ),

        // Quick Metrics Strip
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
          decoration: BoxDecoration(
            color: AppColors.surfaceLow,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.surfaceContainer),
          ),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: AppColors.emeraldAccent,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    const Text('5/5 Онлайн', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.speed, size: 14, color: AppColors.secondary),
                    SizedBox(width: 6),
                    Text('Пинг: ', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    Text('18ms', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.memory, size: 14, color: AppColors.amberAccent),
                    SizedBox(width: 6),
                    Text('Кластер CPU: ', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    Text('28.4%', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textPrimary)),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildControlsBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              // Auto-refresh switch
              Row(
                children: [
                  Switch(
                    value: _autoRefresh,
                    activeColor: AppColors.secondary,
                    onChanged: (v) => setState(() => _autoRefresh = v),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      color: _autoRefresh ? AppColors.secondary : AppColors.outline,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text(
                    'Автоопрос метрик (5s)',
                    style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                  ),
                ],
              ),
              const SizedBox(width: 24),

              // Level Filter Dropdown
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    value: _selectedLevel,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                    items: const [
                      DropdownMenuItem(value: 'ALL', child: Text('Все уровни (INFO, WARN, ERROR)')),
                      DropdownMenuItem(value: 'INFO', child: Text('Только INFO')),
                      DropdownMenuItem(value: 'WARNING', child: Text('Предупреждения WARN')),
                      DropdownMenuItem(value: 'ERROR', child: Text('Ошибки ERROR')),
                    ],
                    onChanged: (v) => setState(() => _selectedLevel = v ?? 'ALL'),
                  ),
                ),
              ),
            ],
          ),

          // Right: Refresh button and Last synced
          Row(
            children: [
              ElevatedButton.icon(
                onPressed: () => _loadData(),
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Обновить статус сейчас'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.secondary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
              ),
              const SizedBox(width: 14),
              Row(
                children: [
                  const Text('Синхронизировано: ', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                  Text(
                    _lastSyncedTime,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHealthSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: const [
                Icon(Icons.hub_outlined, color: AppColors.secondary, size: 20),
                SizedBox(width: 8),
                Text(
                  'Состояние микросервисов и инференса',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: AppColors.primary,
                    fontFamily: 'Plus Jakarta Sans',
                  ),
                ),
              ],
            ),
            const Text('5 активных pod-контейнеров', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
          ],
        ),
        const SizedBox(height: 14),

        // Grid of 5 microservice cards
        Row(
          children: [
            Expanded(
              child: _buildServiceCard(
                name: 'APIGateway',
                role: 'Edge Reverse Proxy & Auth',
                metric1Label: 'Задержка',
                metric1Val: '12ms',
                metric2Label: 'Аптайм',
                metric2Val: '99.98%',
                metric3Label: 'Нагрузка',
                metric3Val: '240 rps',
                icon: Icons.dns_outlined,
                percent: 0.42,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _buildServiceCard(
                name: 'DBConnector',
                role: 'PostgreSQL & ORM layer',
                metric1Label: 'Pool БД',
                metric1Val: '24/50 act',
                metric2Label: 'Ping БД',
                metric2Val: '4ms',
                metric3Label: 'Транзакции',
                metric3Val: '118 tps',
                icon: Icons.storage_outlined,
                percent: 0.48,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _buildServiceCard(
                name: 'LLMConvertor',
                role: 'Gemma-3 Ollama Engine',
                metric1Label: 'Инференс',
                metric1Val: '1.8s',
                metric2Label: 'VRAM',
                metric2Val: '7.8/16 GB',
                metric3Label: 'Очередь',
                metric3Val: '0 docs',
                icon: Icons.psychology_outlined,
                percent: 0.52,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _buildServiceCard(
                name: 'MDConvertor',
                role: 'MarkItDown Ingestion',
                metric1Label: 'Воркер',
                metric1Val: 'Активен',
                metric2Label: 'Задержка',
                metric2Val: '180ms',
                metric3Label: 'Поток',
                metric3Val: '15 doc/min',
                icon: Icons.transform_outlined,
                percent: 0.35,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: _buildServiceCard(
                name: 'JSONToWord',
                role: 'docxtpl Render Engine',
                metric1Label: 'Рендеринг',
                metric1Val: '90ms',
                metric2Label: 'S3 Sync',
                metric2Val: 'Instant',
                metric3Label: 'Качество',
                metric3Val: '100% QA',
                icon: Icons.article_outlined,
                percent: 0.28,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildServiceCard({
    required String name,
    required String role,
    required String metric1Label,
    required String metric1Val,
    required String metric2Label,
    required String metric2Val,
    required String metric3Label,
    required String metric3Val,
    required IconData icon,
    required double percent,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceLow,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(icon, size: 16, color: AppColors.secondary),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    name,
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.emeraldBg,
                  borderRadius: BorderRadius.circular(9999),
                ),
                child: const Text('Healthy', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.emeraldText)),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(role, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
          const SizedBox(height: 14),

          _buildMetricRow(metric1Label, metric1Val),
          const SizedBox(height: 4),
          _buildMetricRow(metric2Label, metric2Val),
          const SizedBox(height: 4),
          _buildMetricRow(metric3Label, metric3Val),
          const SizedBox(height: 12),

          ClipRRect(
            borderRadius: BorderRadius.circular(9999),
            child: LinearProgressIndicator(
              value: percent,
              minHeight: 4,
              backgroundColor: AppColors.surfaceLow,
              valueColor: const AlwaysStoppedAnimation<Color>(AppColors.secondary),
            ),
          ),
          const SizedBox(height: 4),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              'Емкость: ${(percent * 100).toInt()}%',
              style: const TextStyle(fontSize: 10, color: AppColors.outline),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textMuted)),
        Text(value, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
      ],
    );
  }

  Widget _buildLogsSection() {
    final list = _filteredLogs;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Logs Section Header
          Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    const Icon(Icons.terminal_rounded, color: AppColors.secondary, size: 20),
                    const SizedBox(width: 8),
                    const Text(
                      'Журнал системных событий (Real-time Logs)',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                        fontFamily: 'Plus Jakarta Sans',
                      ),
                    ),
                    const SizedBox(width: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceLow,
                        borderRadius: BorderRadius.circular(9999),
                      ),
                      child: Text(
                        '${list.length} записей',
                        style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.secondary),
                      ),
                    ),
                  ],
                ),
                Row(
                  children: [
                    SizedBox(
                      width: 240,
                      height: 36,
                      child: TextField(
                        onChanged: (v) => setState(() => _logSearchQuery = v),
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.search, size: 16),
                          hintText: 'Поиск по тексту лога...',
                          contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    OutlinedButton.icon(
                      onPressed: _copyAllLogs,
                      icon: const Icon(Icons.copy, size: 14),
                      label: const Text('Копировать логи', style: TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const Divider(height: 1, color: AppColors.outlineVariant),

          // Terminal Dark Log Viewer
          Container(
            height: 480,
            color: AppColors.primary,
            padding: const EdgeInsets.all(16),
            child: list.isEmpty
                ? const Center(
                    child: Text(
                      'Логи отсутствуют или загружаются...',
                      style: TextStyle(color: Color(0xFF94A3B8), fontFamily: 'monospace'),
                    ),
                  )
                : ListView.builder(
                    itemCount: list.length,
                    itemBuilder: (context, index) {
                      final item = list[index];
                      Color levelColor = AppColors.emeraldAccent;
                      if (item.level.toUpperCase() == 'ERROR') levelColor = AppColors.roseText;
                      if (item.level.toUpperCase() == 'WARNING' || item.level.toUpperCase() == 'WARN') {
                        levelColor = AppColors.amberAccent;
                      }

                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 3),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Timestamp
                            Text(
                              item.timestamp.length >= 19 ? item.timestamp.substring(11, 19) : item.timestamp,
                              style: const TextStyle(
                                color: Color(0xFF64748B),
                                fontSize: 12,
                                fontFamily: 'monospace',
                              ),
                            ),
                            const SizedBox(width: 10),

                            // Level Badge
                            Container(
                              width: 58,
                              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                              decoration: BoxDecoration(
                                color: levelColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                item.level.toUpperCase(),
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  color: levelColor,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),

                            // Service tag
                            Text(
                              '[${item.service}]',
                              style: const TextStyle(
                                color: AppColors.secondary,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                fontFamily: 'monospace',
                              ),
                            ),
                            const SizedBox(width: 10),

                            // Message
                            Expanded(
                              child: Text(
                                item.message,
                                style: const TextStyle(
                                  color: Color(0xFFF1F5F9),
                                  fontSize: 12,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
