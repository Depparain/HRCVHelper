import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/api_service.dart';

class UploadCVDialog extends StatefulWidget {
  final int hrId;

  const UploadCVDialog({super.key, required this.hrId});

  @override
  State<UploadCVDialog> createState() => _UploadCVDialogState();
}

class _UploadCVDialogState extends State<UploadCVDialog> {
  PlatformFile? _selectedFile;
  bool _isUploading = false;
  double _progressValue = 0.0;
  String _currentStepText = '';
  int _activeStepIndex = 0; // 0, 1, 2, 3
  String? _errorMessage;

  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'docx', 'doc', 'rtf', 'txt', 'md'],
        withData: true,
      );

      if (result != null && result.files.isNotEmpty) {
        setState(() {
          _selectedFile = result.files.first;
          _errorMessage = null;
          _progressValue = 0.0;
          _activeStepIndex = 0;
        });
      }
    } catch (e) {
      setState(() => _errorMessage = 'Ошибка выбора файла: $e');
    }
  }

  Future<void> _startParsing() async {
    if (_selectedFile == null || _selectedFile!.bytes == null) return;

    setState(() {
      _isUploading = true;
      _errorMessage = null;
      _activeStepIndex = 1;
      _progressValue = 0.25;
      _currentStepText = 'Загрузка файла во временное хранилище...';
    });

    try {
      // Имитируем прогресс пайплайна для визуального отклика
      Future.delayed(const Duration(milliseconds: 500), () {
        if (mounted && _isUploading) {
          setState(() {
            _activeStepIndex = 2;
            _progressValue = 0.60;
            _currentStepText = 'Извлечение текста и нормализация разметки (MarkItDown)...';
          });
        }
      });

      Future.delayed(const Duration(milliseconds: 1200), () {
        if (mounted && _isUploading) {
          setState(() {
            _activeStepIndex = 3;
            _progressValue = 0.85;
            _currentStepText = 'Структурирование моделью Gemma-3 (152-ФЗ)...';
          });
        }
      });

      final record = await apiService.uploadCV(
        _selectedFile!.bytes!,
        _selectedFile!.name,
        widget.hrId,
      );

      if (mounted) {
        setState(() {
          _progressValue = 1.0;
          _activeStepIndex = 4;
          _currentStepText = 'Готово! Переход к валидации HR...';
          _isUploading = false;
        });

        Navigator.of(context).pop(record);
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isUploading = false;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      insetPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
      child: Container(
        constraints: const BoxConstraints(maxWidth: 820),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Modal Top Header Bar
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 24, 20, 16),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AppColors.surfaceLow,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Center(
                      child: Icon(
                        Icons.cloud_upload_outlined,
                        size: 24,
                        color: AppColors.secondary,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'Загрузка документа',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                color: AppColors.primary,
                                fontFamily: 'Plus Jakarta Sans',
                              ),
                            ),
                            const SizedBox(width: 10),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceContainer,
                                borderRadius: BorderRadius.circular(9999),
                              ),
                              child: const Text(
                                'CVHelper AI v3.2',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.secondary,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Поддерживаемые форматы: PDF, DOCX, RTF (до 25 МБ)',
                          style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: _isUploading ? null : () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.close, size: 20, color: AppColors.textMuted),
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.surfaceLow,
                      shape: const CircleBorder(),
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1, color: AppColors.outlineVariant),

            // Modal Body
            Padding(
              padding: const EdgeInsets.all(28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Dropzone Card
                  InkWell(
                    onTap: _isUploading ? null : _pickFile,
                    borderRadius: BorderRadius.circular(16),
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
                      decoration: BoxDecoration(
                        color: const Color(0xFFEFF6FF),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(
                          color: const Color(0xFF93C5FD),
                          width: 1.8,
                          strokeAlign: BorderSide.strokeAlignInside,
                        ),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            width: 56,
                            height: 56,
                            decoration: const BoxDecoration(
                              color: Colors.white,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: Color(0x0D091426),
                                  blurRadius: 10,
                                  offset: Offset(0, 4),
                                ),
                              ],
                            ),
                            child: const Icon(
                              Icons.upload_file_rounded,
                              size: 30,
                              color: AppColors.secondary,
                            ),
                          ),
                          const SizedBox(height: 14),
                          const Text(
                            'Перетащите файлы в это окно',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                              color: AppColors.primary,
                              fontFamily: 'Plus Jakarta Sans',
                            ),
                          ),
                          const SizedBox(height: 4),
                          const Text(
                            'или выберите локальный документ на компьютере',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.textMuted,
                            ),
                          ),
                          const SizedBox(height: 16),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(9999),
                              boxShadow: const [
                                BoxShadow(
                                  color: Color(0x0A091426),
                                  blurRadius: 6,
                                  offset: Offset(0, 2),
                                ),
                              ],
                            ),
                            child: const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.add_circle_outline, size: 16, color: AppColors.primary),
                                SizedBox(width: 6),
                                Text(
                                  'Выбрать файл',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.primary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // Selected File Preview Card
                  if (_selectedFile != null) ...[
                    const SizedBox(height: 20),
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceLow,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.surfaceContainer),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Container(
                                width: 42,
                                height: 42,
                                decoration: BoxDecoration(
                                  color: AppColors.surfaceContainer,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: const Icon(
                                  Icons.picture_as_pdf_rounded,
                                  size: 22,
                                  color: AppColors.secondary,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      _selectedFile!.name,
                                      style: const TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.textPrimary,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 2),
                                    Row(
                                      children: [
                                        Text(
                                          '${(_selectedFile!.size / (1024 * 1024)).toStringAsFixed(1)} MB',
                                          style: const TextStyle(
                                            fontSize: 12,
                                            color: AppColors.textMuted,
                                          ),
                                        ),
                                        const SizedBox(width: 8),
                                        const Text('•', style: TextStyle(color: AppColors.textMuted)),
                                        const SizedBox(width: 8),
                                        const Icon(
                                          Icons.verified_user_rounded,
                                          size: 14,
                                          color: AppColors.emeraldText,
                                        ),
                                        const SizedBox(width: 4),
                                        const Text(
                                          'Файл проверен',
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: AppColors.emeraldText,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              if (!_isUploading)
                                IconButton(
                                  onPressed: () => setState(() => _selectedFile = null),
                                  icon: const Icon(
                                    Icons.delete_outline,
                                    color: AppColors.error,
                                    size: 20,
                                  ),
                                  tooltip: 'Удалить',
                                ),
                            ],
                          ),

                          // Progress bar if uploading
                          if (_isUploading) ...[
                            const SizedBox(height: 14),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.between,
                              children: [
                                Text(
                                  _currentStepText,
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: AppColors.textSecondary,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                                Text(
                                  '${(_progressValue * 100).toInt()}%',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.secondary,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(9999),
                              child: LinearProgressIndicator(
                                value: _progressValue,
                                minHeight: 6,
                                backgroundColor: AppColors.surfaceContainer,
                                valueColor: const AlwaysStoppedAnimation<Color>(AppColors.secondary),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                  ],

                  // Pipeline Steps Card
                  const SizedBox(height: 20),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: AppColors.outlineVariant),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'ЭТАПЫ ИНТЕЛЛЕКТУАЛЬНОГО ПАЙПЛАЙНА',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                            color: AppColors.textMuted,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _buildStepRow(
                          stepNumber: 1,
                          title: '1. Загрузка файла',
                          subtitle: 'Стриминг во временное S3-хранилище',
                          isDone: _activeStepIndex > 1,
                          isActive: _activeStepIndex == 1,
                        ),
                        const SizedBox(height: 8),
                        _buildStepRow(
                          stepNumber: 2,
                          title: '2. Извлечение текста и OCR',
                          subtitle: 'MarkItDown + разметка Markdown',
                          isDone: _activeStepIndex > 2,
                          isActive: _activeStepIndex == 2,
                        ),
                        const SizedBox(height: 8),
                        _buildStepRow(
                          stepNumber: 3,
                          title: '3. Структурирование моделью Gemma-3',
                          subtitle: 'Нормализация скиллов, проектов и 152-ФЗ валидация',
                          isDone: _activeStepIndex > 3,
                          isActive: _activeStepIndex == 3,
                        ),
                      ],
                    ),
                  ),

                  // Error Banner
                  if (_errorMessage != null) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.errorContainer,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: AppColors.roseBorder),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.error_outline, color: AppColors.error, size: 20),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _errorMessage!,
                              style: const TextStyle(color: AppColors.error, fontSize: 13),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // Modal Footer Actions
            Padding(
              padding: const EdgeInsets.fromLTRB(28, 0, 28, 24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  OutlinedButton(
                    onPressed: _isUploading ? null : () => Navigator.of(context).pop(),
                    child: const Text('Отмена'),
                  ),
                  const SizedBox(width: 12),
                  ElevatedButton.icon(
                    onPressed: (_selectedFile == null || _isUploading) ? null : _startParsing,
                    icon: _isUploading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.play_arrow_rounded, size: 18),
                    label: Text(_isUploading ? 'Обработка...' : 'Начать парсинг'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.secondary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepRow({
    required int stepNumber,
    required String title,
    required String subtitle,
    required bool isDone,
    required bool isActive,
  }) {
    Color iconBg = AppColors.surfaceLow;
    Widget iconChild = Icon(
      isDone ? Icons.check : Icons.circle_outlined,
      size: 14,
      color: isDone ? AppColors.emeraldText : AppColors.outline,
    );

    if (isActive) {
      iconBg = AppColors.secondary;
      iconChild = const SizedBox(
        width: 12,
        height: 12,
        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
      );
    } else if (isDone) {
      iconBg = AppColors.emeraldBg;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: isActive ? AppColors.surfaceLow : Colors.transparent,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              color: iconBg,
              shape: BoxShape.circle,
            ),
            child: Center(child: iconChild),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: isActive ? AppColors.secondary : AppColors.textPrimary,
                  ),
                ),
                Text(
                  subtitle,
                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          if (isDone)
            const Text(
              'Завершено ✓',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.emeraldText,
              ),
            )
          else if (isActive)
            const Text(
              'В процессе...',
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: AppColors.secondary,
              ),
            ),
        ],
      ),
    );
  }
}
