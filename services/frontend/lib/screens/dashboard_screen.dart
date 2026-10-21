import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/auth_provider.dart';
import '../services/api_service.dart';
import 'login_screen.dart';
import 'validation_screen.dart';
import 'admin_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<CVRecord> _recentCVs = [];
  bool _isLoadingHistory = false;

  // Состояние загрузки файла
  PlatformFile? _selectedFile;
  bool _isUploading = false;
  String _uploadStep = '';
  double _progressValue = 0.0;
  String? _uploadError;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    if (auth.currentUser == null) return;

    setState(() => _isLoadingHistory = true);
    try {
      final cvs = await apiService.listCVs(hrId: auth.currentUser!.hrId);
      if (mounted) {
        setState(() {
          _recentCVs = cvs;
          _isLoadingHistory = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoadingHistory = false);
    }
  }

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'doc', 'txt', 'md'],
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedFile = result.files.first;
          _uploadError = null;
        });
      }
    } catch (e) {
      setState(() => _uploadError = 'Ошибка выбора файла: $e');
    }
  }

  Future<void> _startParsing() async {
    if (_selectedFile == null || _selectedFile!.bytes == null) return;

    final auth = Provider.of<AuthProvider>(context, listen: false);
    setState(() {
      _isUploading = true;
      _uploadError = null;
      _progressValue = 0.25;
      _uploadStep = '1/3: Загрузка и конвертация в Markdown (MarkItDown)...';
    });

    try {
      // Имитация этапов для плавного UI
      Future.delayed(const Duration(milliseconds: 600), () {
        if (mounted && _isUploading) {
          setState(() {
            _progressValue = 0.65;
            _uploadStep = '2/3: Семантический парсинг локальной моделью Gemma-3 (152-ФЗ)...';
          });
        }
      });

      final record = await apiService.uploadCV(
        _selectedFile!.bytes!,
        _selectedFile!.name,
        auth.currentUser?.hrId ?? 1,
      );

      if (mounted) {
        setState(() {
          _progressValue = 1.0;
          _uploadStep = '3/3: Готово! Переход к валидации HR...';
          _isUploading = false;
          _selectedFile = null;
        });

        _loadHistory();

        // Переходим к окну интерактивной валидации
        Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => ValidationScreen(
              cvId: record.cvId,
              initialData: record.jsonData,
            ),
          ),
        ).then((_) => _loadHistory());
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isUploading = false;
          _uploadError = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final user = auth.currentUser;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Icon(Icons.description, color: AppColors.primary),
            const SizedBox(width: 8),
            const Text('HRCVHelper'),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.2),
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text('HR Workspace', style: TextStyle(fontSize: 11, color: AppColors.primary)),
            ),
          ],
        ),
        actions: [
          TextButton.icon(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const AdminScreen()),
              );
            },
            icon: const Icon(Icons.admin_panel_settings_outlined, size: 18),
            label: const Text('Админ-панель'),
          ),
          const SizedBox(width: 8),
          Chip(
            avatar: const CircleAvatar(
              backgroundColor: AppColors.primary,
              child: Icon(Icons.person, size: 14, color: Colors.white),
            ),
            label: Text(user?.fullName ?? 'HR-специалист'),
            backgroundColor: AppColors.surfaceLight,
          ),
          IconButton(
            icon: const Icon(Icons.logout, size: 20),
            tooltip: 'Выйти',
            onPressed: () {
              auth.logout();
              Navigator.of(context).pushReplacement(
                MaterialPageRoute(builder: (_) => const LoginScreen()),
              );
            },
          ),
          const SizedBox(width: 16),
        ],
      ),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1100),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              // Карточка загрузки
              _buildUploadCard(),
              const SizedBox(height: 32),

              // История резюме
              _buildHistorySection(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUploadCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Row(
              children: [
                Icon(Icons.cloud_upload_outlined, color: AppColors.secondary, size: 24),
                SizedBox(width: 10),
                Text(
                  'Загрузка резюме на обработку',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Поддерживаются файлы PDF, DOCX, DOC, TXT. Система извлечет текст, переведет в Markdown, структурирует поля в JSON через Gemma-3 и откроет форму для проверки.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 24),

            // Дропзона
            InkWell(
              onTap: _isUploading ? null : _pickFile,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
                decoration: BoxDecoration(
                  color: AppColors.background,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: _selectedFile != null ? AppColors.primary : AppColors.border,
                    width: 1.5,
                  ),
                ),
                child: Column(
                  children: [
                    Icon(
                      _selectedFile != null ? Icons.insert_drive_file : Icons.upload_file,
                      size: 44,
                      color: _selectedFile != null ? AppColors.primary : AppColors.textMuted,
                    ),
                    const SizedBox(height: 12),
                    if (_selectedFile != null) ...[
                      Text(
                        _selectedFile!.name,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Размер: ${(_selectedFile!.size / 1024).toStringAsFixed(1)} КБ',
                        style: const TextStyle(color: AppColors.textSecondary, fontSize: 12),
                      ),
                    ] else ...[
                      const Text(
                        'Нажмите, чтобы выбрать файл резюме',
                        style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'PDF, Word (.docx), Markdown или TXT',
                        style: TextStyle(color: AppColors.textMuted, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            if (_uploadError != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.error.withOpacity(0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: AppColors.error, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(_uploadError!, style: const TextStyle(color: AppColors.error, fontSize: 13)),
                    ),
                  ],
                ),
              ),
            ],

            // Индикатор прогресса
            if (_isUploading) ...[
              const SizedBox(height: 20),
              LinearProgressIndicator(value: _progressValue, backgroundColor: AppColors.border, color: AppColors.primary),
              const SizedBox(height: 8),
              Text(
                _uploadStep,
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.secondary, fontSize: 13, fontWeight: FontWeight.w500),
              ),
            ],

            const SizedBox(height: 20),

            // Кнопка запуска
            if (_selectedFile != null && !_isUploading)
              ElevatedButton.icon(
                onPressed: _startParsing,
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Распознать и структурировать через Gemma-3'),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistorySection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.history, color: AppColors.primary, size: 22),
            const SizedBox(width: 8),
            const Text(
              'Обработанные резюме',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const Spacer(),
            IconButton(
              icon: const Icon(Icons.refresh, size: 20),
              onPressed: _loadHistory,
              tooltip: 'Обновить список',
            ),
          ],
        ),
        const SizedBox(height: 12),

        if (_isLoadingHistory)
          const Center(child: Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator()))
        else if (_recentCVs.isEmpty)
          Card(
            child: Container(
              padding: const EdgeInsets.all(36),
              alignment: Alignment.center,
              child: const Text(
                'Пока нет загруженных резюме. Загрузите первый файл выше.',
                style: TextStyle(color: AppColors.textSecondary),
              ),
            ),
          )
        else
          Card(
            child: ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: _recentCVs.length,
              separatorBuilder: (_, __) => const Divider(color: AppColors.border, height: 1),
              itemBuilder: (ctx, index) {
                final cv = _recentCVs[index];
                return ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                  leading: CircleAvatar(
                    backgroundColor: AppColors.surfaceLight,
                    child: Text('#${cv.cvId}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                  ),
                  title: Text(
                    cv.jsonData.fio.isNotEmpty ? cv.jsonData.fio : 'Кандидат #${cv.cvId}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text(
                    cv.jsonData.vacancy.isNotEmpty ? cv.jsonData.vacancy : 'Вакансия не указана',
                    style: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
                  ),
                  trailing: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _buildStatusChip(cv.status),
                      const SizedBox(width: 12),
                      if (cv.status == 'Ожидает проверки HR')
                        ElevatedButton.icon(
                          onPressed: () {
                            Navigator.of(context).push(
                              MaterialPageRoute(
                                builder: (_) => ValidationScreen(
                                  cvId: cv.cvId,
                                  initialData: cv.jsonData,
                                ),
                              ),
                            ).then((_) => _loadHistory());
                          },
                          icon: const Icon(Icons.edit_note, size: 16),
                          label: const Text('Проверить'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                          ),
                        )
                      else if (cv.status == 'Готово')
                        OutlinedButton.icon(
                          onPressed: () async {
                            final url = '${apiService.getDownloadUrl(cv.cvId)}';
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Файл готов к скачиванию: $url')),
                            );
                          },
                          icon: const Icon(Icons.download, size: 16, color: AppColors.success),
                          label: const Text('Скачать .docx'),
                        ),
                    ],
                  ),
                );
              },
            ),
          ),
      ],
    );
  }

  Widget _buildStatusChip(String status) {
    Color bg = AppColors.surfaceLight;
    Color fg = AppColors.textPrimary;

    if (status == 'Готово') {
      bg = AppColors.success.withOpacity(0.2);
      fg = AppColors.success;
    } else if (status == 'Ожидает проверки HR') {
      bg = AppColors.warning.withOpacity(0.2);
      fg = AppColors.warning;
    } else {
      bg = AppColors.info.withOpacity(0.2);
      fg = AppColors.info;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withOpacity(0.5)),
      ),
      child: Text(
        status,
        style: TextStyle(color: fg, fontSize: 12, fontWeight: FontWeight.bold),
      ),
    );
  }
}
