import 'dart:async';
import 'package:flutter/material.dart';
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
  Timer? _refreshTimer;
  bool _autoRefresh = true;

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

      if (mounted) {
        setState(() {
          _healthReport = health;
          _logs = logs;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  List<LogItem> get _filteredLogs {
    if (_selectedLevel == 'ALL') return _logs;
    return _logs.where((l) => l.level.toUpperCase() == _selectedLevel).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Панель администратора — Мониторинг и логи системы'),
        actions: [
          Row(
            children: [
              const Text('Автообновление', style: TextStyle(fontSize: 13, color: AppColors.textSecondary)),
              Switch(
                value: _autoRefresh,
                onChanged: (v) => setState(() => _autoRefresh = v),
                activeColor: AppColors.primary,
              ),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _loadData(),
            tooltip: 'Обновить данные',
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: _isLoading && _healthReport == null
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                // 1. Сводка здоровья (Health report)
                _buildHealthSection(),
                const SizedBox(height: 28),

                // 2. Системные логи
                _buildLogsSection(),
              ],
            ),
    );
  }

  Widget _buildHealthSection() {
    final isAllHealthy = _healthReport?.isHealthy ?? false;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isAllHealthy ? Icons.check_circle : Icons.warning_amber_rounded,
                  color: isAllHealthy ? AppColors.success : AppColors.warning,
                  size: 24,
                ),
                const SizedBox(width: 10),
                const Text(
                  'Работоспособность контейнеров и сервисов (Health Report)',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                if (_healthReport != null)
                  Text(
                    'Статус: ${_healthReport!.status.toUpperCase()}',
                    style: TextStyle(
                      color: isAllHealthy ? AppColors.success : AppColors.warning,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),

            if (_healthReport == null)
              const Text('Нет данных о состоянии системы', style: TextStyle(color: AppColors.textSecondary))
            else
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: _healthReport!.services.entries.map((entry) {
                  final s = entry.value;
                  return _buildServiceHealthChip(s);
                }).toList(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildServiceHealthChip(ServiceStatus s) {
    final ok = s.isHealthy;
    final color = ok ? AppColors.success : AppColors.error;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surfaceLight,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            s.service,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
          ),
          const SizedBox(width: 6),
          Text(
            s.status,
            style: TextStyle(color: color, fontSize: 11),
          ),
        ],
      ),
    );
  }

  Widget _buildLogsSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.list_alt, color: AppColors.secondary, size: 22),
                const SizedBox(width: 10),
                const Text(
                  'Системные логи контейнеров',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                ),
                const Spacer(),

                // Фильтры логов
                SegmentedButton<String>(
                  segments: const [
                    ButtonSegment(value: 'ALL', label: Text('Все')),
                    ButtonSegment(value: 'INFO', label: Text('INFO')),
                    ButtonSegment(value: 'WARNING', label: Text('WARN')),
                    ButtonSegment(value: 'ERROR', label: Text('ERR')),
                  ],
                  selected: {_selectedLevel},
                  onSelectionChanged: (val) {
                    setState(() => _selectedLevel = val.first);
                  },
                ),
              ],
            ),
            const SizedBox(height: 16),

            if (_filteredLogs.isEmpty)
              Container(
                height: 180,
                alignment: Center(
                  child: Text(
                    'Нет записей в журнале логов',
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                ),
              )
            else
              Container(
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.border),
                ),
                constraints: const BoxConstraints(maxHeight: 450),
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: _filteredLogs.length,
                  separatorBuilder: (_, __) => const Divider(color: AppColors.border, height: 1),
                  itemBuilder: (ctx, index) {
                    final log = _filteredLogs[index];
                    Color badgeColor = AppColors.info;
                    if (log.level.toUpperCase() == 'ERROR') badgeColor = AppColors.error;
                    if (log.level.toUpperCase() == 'WARNING') badgeColor = AppColors.warning;

                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: badgeColor.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(4),
                              border: Border.all(color: badgeColor.withOpacity(0.4)),
                            ),
                            child: Text(
                              log.level.toUpperCase(),
                              style: TextStyle(color: badgeColor, fontSize: 10, fontWeight: FontWeight.bold),
                            ),
                          ),
                          const SizedBox(width: 10),
                          Text(
                            log.timestamp.length >= 19 ? log.timestamp.substring(11, 19) : log.timestamp,
                            style: const TextStyle(fontSize: 12, color: AppColors.textMuted, fontFamily: 'monospace'),
                          ),
                          const SizedBox(width: 12),
                          Text(
                            '[${log.service}]',
                            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w600),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              log.message,
                              style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
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
      ),
    );
  }
}
