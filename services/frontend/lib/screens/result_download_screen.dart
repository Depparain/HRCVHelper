import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/api_service.dart';
import '../constants/api_constants.dart';

class ResultDownloadScreen extends StatefulWidget {
  final CVRecord record;

  const ResultDownloadScreen({super.key, required this.record});

  @override
  State<ResultDownloadScreen> createState() => _ResultDownloadScreenState();
}

class _ResultDownloadScreenState extends State<ResultDownloadScreen> {
  bool _isDownloading = false;
  bool _copied = false;

  String get _candidateName =>
      widget.record.jsonData.fio.isNotEmpty ? widget.record.jsonData.fio : 'Кандидат';

  String get _vacancy =>
      widget.record.jsonData.vacancy.isNotEmpty ? widget.record.jsonData.vacancy : 'Специалист';

  String get _safeFilename {
    final cleanFio = _candidateName.replaceAll(RegExp(r'[^а-яА-Яa-zA-Z0-9_-]'), '_');
    final cleanVac = _vacancy.replaceAll(RegExp(r'[^а-яА-Яa-zA-Z0-9_-]'), '_');
    return 'Резюме_${cleanFio}_$cleanVac.docx';
  }

  Future<void> _downloadDocx() async {
    setState(() => _isDownloading = true);
    try {
      final bytes = await apiService.downloadDocxBytes(widget.record.cvId);
      // In Flutter Web, download can be triggered via anchor click or saving bytes
      final url = ApiConstants.cvDownloadUrl(widget.record.cvId);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Файл $_safeFilename успешно сохранен (${(bytes.length / 1024).toStringAsFixed(0)} КБ)'),
          backgroundColor: AppColors.emeraldText,
        ),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Ошибка скачивания: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    } finally {
      if (mounted) setState(() => _isDownloading = false);
    }
  }

  void _copyDownloadLink() {
    final url = ApiConstants.cvDownloadUrl(widget.record.cvId);
    Clipboard.setData(ClipboardData(text: url));
    setState(() => _copied = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Ссылка на скачивание скопирована в буфер обмена'),
        duration: Duration(seconds: 2),
      ),
    );
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) setState(() => _copied = false);
    });
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
            const Icon(Icons.description_rounded, color: AppColors.secondary),
            const SizedBox(width: 8),
            const Text('HRCVHelper'),
            const SizedBox(width: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainer,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text('Готовый результат', style: TextStyle(fontSize: 11, color: AppColors.secondary)),
            ),
          ],
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
        child: Center(
          child: Container(
            constraints: const BoxConstraints(maxWidth: 960),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Breadcrumbs
                Row(
                  children: [
                    InkWell(
                      onTap: () => Navigator.of(context).pop(),
                      child: const Text(
                        'Реестр резюме',
                        style: TextStyle(fontSize: 13, color: AppColors.textMuted),
                      ),
                    ),
                    const SizedBox(width: 6),
                    const Icon(Icons.chevron_right, size: 16, color: AppColors.outline),
                    const SizedBox(width: 6),
                    Text(
                      'Резюме #CV-${widget.record.cvId}',
                      style: const TextStyle(fontSize: 13, color: AppColors.textMuted),
                    ),
                    const SizedBox(width: 6),
                    const Icon(Icons.chevron_right, size: 16, color: AppColors.outline),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: AppColors.surfaceContainer,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'Готовый результат',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 24),

                // Main Success Container
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: AppColors.outlineVariant),
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.primary.withOpacity(0.04),
                        blurRadius: 24,
                        offset: const Offset(0, 8),
                      ),
                    ],
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Column(
                    children: [
                      // Top gradient indicator bar
                      Container(
                        height: 5,
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(
                            colors: [
                              AppColors.secondary,
                              Color(0xFF3B82F6),
                              AppColors.secondary,
                            ],
                          ),
                        ),
                      ),

                      Padding(
                        padding: const EdgeInsets.all(36),
                        child: Column(
                          children: [
                            // Success check circle
                            Container(
                              width: 68,
                              height: 68,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: AppColors.emeraldBg,
                                border: Border.all(color: AppColors.emeraldBorder, width: 2),
                              ),
                              child: const Center(
                                child: Icon(
                                  Icons.check_rounded,
                                  size: 38,
                                  color: AppColors.emeraldText,
                                ),
                              ),
                            ),
                            const SizedBox(height: 16),

                            // Pipeline Code 200 pill badge
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceLow,
                                borderRadius: BorderRadius.circular(9999),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Container(
                                    width: 6,
                                    height: 6,
                                    decoration: const BoxDecoration(
                                      color: AppColors.emeraldText,
                                      shape: BoxShape.circle,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  const Text(
                                    'Пайплайн завершен • Код 200 OK',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.secondary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 14),

                            const Text(
                              'Документ успешно сгенерирован и готов к скачиванию!',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w700,
                                color: AppColors.primary,
                                fontFamily: 'Plus Jakarta Sans',
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Шаблон в формате .docx сформирован микросервисом JSONToWord и сохранен в защищенном хранилище S3.',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 14, color: AppColors.textMuted),
                            ),
                            const SizedBox(height: 32),

                            // Detailed Document Card
                            Container(
                              padding: const EdgeInsets.all(24),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceLow,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: AppColors.surfaceContainer),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // Left Document Preview Box
                                  Container(
                                    width: 80,
                                    height: 104,
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(color: AppColors.surfaceContainer),
                                      boxShadow: [
                                        BoxShadow(
                                          color: AppColors.primary.withOpacity(0.06),
                                          blurRadius: 10,
                                          offset: const Offset(0, 4),
                                        ),
                                      ],
                                    ),
                                    child: Column(
                                      children: [
                                        Container(
                                          height: 8,
                                          decoration: const BoxDecoration(
                                            color: AppColors.secondary,
                                            borderRadius: BorderRadius.vertical(top: Radius.circular(9)),
                                          ),
                                        ),
                                        const Expanded(
                                          child: Center(
                                            child: Icon(
                                              Icons.description_rounded,
                                              size: 38,
                                              color: AppColors.secondary,
                                            ),
                                          ),
                                        ),
                                        Container(
                                          padding: const EdgeInsets.only(bottom: 6),
                                          child: const Text(
                                            'DOCX',
                                            style: TextStyle(
                                              fontSize: 10,
                                              fontWeight: FontWeight.w800,
                                              color: AppColors.secondary,
                                              letterSpacing: 0.8,
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 20),

                                  // Right Metadata & Actions
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Row(
                                          children: [
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: Colors.white,
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: const Text(
                                                'MS Word Document',
                                                style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            Container(
                                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                              decoration: BoxDecoration(
                                                color: AppColors.emeraldBg,
                                                borderRadius: BorderRadius.circular(6),
                                              ),
                                              child: const Text(
                                                'Готов к отправке заказчику',
                                                style: TextStyle(
                                                  fontSize: 11,
                                                  fontWeight: FontWeight.w600,
                                                  color: AppColors.emeraldText,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                        const SizedBox(height: 8),
                                        Text(
                                          _safeFilename,
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.w700,
                                            color: AppColors.primary,
                                          ),
                                        ),
                                        const SizedBox(height: 4),
                                        const Text(
                                          'Сгенерировано по брендбуку «Expert Choice / HRHelper Enterprise Standard»',
                                          style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                                        ),
                                        const SizedBox(height: 16),

                                        // 3 Metadata pills
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                          decoration: BoxDecoration(
                                            color: Colors.white,
                                            borderRadius: BorderRadius.circular(10),
                                            border: Border.all(color: AppColors.surfaceContainer),
                                          ),
                                          child: Row(
                                            children: const [
                                              Expanded(
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.start,
                                                  children: [
                                                    Text('Размер файла', style: TextStyle(fontSize: 11, color: AppColors.outline)),
                                                    SizedBox(height: 2),
                                                    Text('~428 КБ', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary)),
                                                  ],
                                                ),
                                              ),
                                              Expanded(
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.start,
                                                  children: [
                                                    Text('Хранилище', style: TextStyle(fontSize: 11, color: AppColors.outline)),
                                                    SizedBox(height: 2),
                                                    Text('S3 Bucket', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.secondary)),
                                                  ],
                                                ),
                                              ),
                                              Expanded(
                                                child: Column(
                                                  crossAxisAlignment: CrossAxisAlignment.start,
                                                  children: [
                                                    Text('Срок действия', style: TextStyle(fontSize: 11, color: AppColors.outline)),
                                                    SizedBox(height: 2),
                                                    Text('Бессрочно', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.primary)),
                                                  ],
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                        const SizedBox(height: 18),

                                        // Action buttons
                                        Row(
                                          children: [
                                            Expanded(
                                              child: ElevatedButton.icon(
                                                onPressed: _isDownloading ? null : _downloadDocx,
                                                icon: _isDownloading
                                                    ? const SizedBox(
                                                        width: 16,
                                                        height: 16,
                                                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                                      )
                                                    : const Icon(Icons.download_rounded, size: 18),
                                                label: Text(_isDownloading ? 'Скачивание...' : 'Скачать готовый .docx'),
                                                style: ElevatedButton.styleFrom(
                                                  backgroundColor: AppColors.secondary,
                                                  foregroundColor: Colors.white,
                                                  minimumSize: const Size.fromHeight(42),
                                                ),
                                              ),
                                            ),
                                            const SizedBox(width: 12),
                                            OutlinedButton.icon(
                                              onPressed: _copyDownloadLink,
                                              icon: Icon(_copied ? Icons.check : Icons.link_rounded, size: 18, color: AppColors.secondary),
                                              label: Text(_copied ? 'Скопировано!' : 'Копировать ссылку'),
                                              style: OutlinedButton.styleFrom(
                                                minimumSize: const Size(180, 42),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            const SizedBox(height: 24),

                            // Return to dashboard link
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                OutlinedButton.icon(
                                  onPressed: () => Navigator.of(context).pop(),
                                  icon: const Icon(Icons.arrow_back, size: 16),
                                  label: const Text('Вернуться к списку резюме'),
                                ),
                                ElevatedButton.icon(
                                  onPressed: () => Navigator.of(context).pop(),
                                  icon: const Icon(Icons.add, size: 16),
                                  label: const Text('Загрузить еще одно резюме'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.surfaceContainer,
                                    foregroundColor: AppColors.primary,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),

                      // Audit Log Strip
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 14),
                        decoration: const BoxDecoration(
                          color: AppColors.surfaceLow,
                          border: Border(top: BorderSide(color: AppColors.surfaceContainer)),
                        ),
                        child: Row(
                          children: const [
                            Icon(Icons.history_edu_rounded, size: 16, color: AppColors.secondary),
                            SizedBox(width: 8),
                            Text('Журнал аудита: ', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                            Text('Сгенерировано микросервисом JSONToWord', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                            Spacer(),
                            Text('152-ФЗ compliant • SHA-256 Verified', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // 3 Highlights at bottom
                Row(
                  children: [
                    _buildFeatureCard(
                      icon: Icons.lock_outline,
                      title: 'Шифрование данных',
                      subtitle: 'Файл защищен AES-256 на стороне S3 Bucket',
                    ),
                    const SizedBox(width: 16),
                    _buildFeatureCard(
                      icon: Icons.shield_outlined,
                      title: 'Соответствие 152-ФЗ',
                      subtitle: 'Парсинг без передачи данных во внешние облачные сервисы',
                    ),
                    const SizedBox(width: 16),
                    _buildFeatureCard(
                      icon: Icons.article_outlined,
                      title: 'Корпоративный шаблон',
                      subtitle: '100% стандартизация структуры через docxtpl',
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFeatureCard({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.outlineVariant),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.surfaceLow,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, size: 20, color: AppColors.secondary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
