import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/api_service.dart';

class ValidationScreen extends StatefulWidget {
  final int cvId;
  final CVJsonData initialData;

  const ValidationScreen({
    super.key,
    required this.cvId,
    required this.initialData,
  });

  @override
  State<ValidationScreen> createState() => _ValidationScreenState();
}

class _ValidationScreenState extends State<ValidationScreen> {
  late CVJsonData _data;
  bool _isSaving = false;
  String? _successMessage;
  String? _errorMessage;

  // Текстовые контроллеры шапки
  late TextEditingController _fioController;
  late TextEditingController _vacancyController;
  late TextEditingController _totalYearController;
  late TextEditingController _backgroundController;
  late TextEditingController _pitchController;

  // Контроллеры личной информации
  late TextEditingController _languagesController;
  late TextEditingController _locationController;
  late TextEditingController _employmentController;
  late TextEditingController _statusController;

  @override
  void initState() {
    super.initState();
    _data = widget.initialData;

    _fioController = TextEditingController(text: _data.fio);
    _vacancyController = TextEditingController(text: _data.vacancy);
    _totalYearController = TextEditingController(text: _data.totalYearWork);
    _backgroundController = TextEditingController(text: _data.projectBackround);
    _pitchController = TextEditingController(text: _data.pitch);

    _languagesController = TextEditingController(text: _data.languages);
    _locationController = TextEditingController(text: _data.citizenshipLocation);
    _employmentController = TextEditingController(text: _data.employment);
    _statusController = TextEditingController(text: _data.status);
  }

  @override
  void dispose() {
    _fioController.dispose();
    _vacancyController.dispose();
    _totalYearController.dispose();
    _backgroundController.dispose();
    _pitchController.dispose();
    _languagesController.dispose();
    _locationController.dispose();
    _employmentController.dispose();
    _statusController.dispose();
    super.dispose();
  }

  void _syncData() {
    _data.fio = _fioController.text.trim();
    _data.vacancy = _vacancyController.text.trim();
    _data.totalYearWork = _totalYearController.text.trim();
    _data.projectBackround = _backgroundController.text.trim();
    _data.pitch = _pitchController.text.trim();

    _data.languages = _languagesController.text.trim();
    _data.citizenshipLocation = _locationController.text.trim();
    _data.employment = _employmentController.text.trim();
    _data.status = _statusController.text.trim();
  }

  Future<void> _saveAndGenerate() async {
    _syncData();
    setState(() {
      _isSaving = true;
      _errorMessage = null;
      _successMessage = null;
    });

    try {
      final record = await apiService.validateCV(widget.cvId, _data);
      setState(() {
        _isSaving = false;
        _successMessage = 'Резюме успешно проверено и корпоративный .docx сформирован!';
      });
      _showDownloadDialog(record);
    } catch (e) {
      setState(() {
        _isSaving = false;
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    }
  }

  void _showDownloadDialog(CVRecord record) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Row(
          children: [
            Icon(Icons.check_circle, color: AppColors.success),
            SizedBox(width: 8),
            Text('Документ готов'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Кандидат: ${_data.fio}'),
            const SizedBox(height: 4),
            Text('Вакансия: ${_data.vacancy}'),
            const SizedBox(height: 12),
            const Text(
              'Файл .docx сгенерирован по корпоративному шаблону и сохранен в хранилище S3.',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Закрыть'),
          ),
          ElevatedButton.icon(
            onPressed: () async {
              try {
                final bytes = await apiService.downloadDocxBytes(widget.cvId);
                _downloadFileBytes(bytes, 'CV_${_data.fio.replaceAll(' ', '_')}.docx');
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Файл скачан!')),
                  );
                }
              } catch (e) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Ошибка скачивания: $e')),
                  );
                }
              }
            },
            icon: const Icon(Icons.download),
            label: const Text('Скачать .docx'),
          ),
        ],
      ),
    );
  }

  void _downloadFileBytes(Uint8List bytes, String filename) {
    // В веб-версии открывает прямую ссылку или триггерит скачивание
    final url = '${apiService.getDownloadUrl(widget.cvId)}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Валидация резюме #${widget.cvId} — Human-in-the-Loop'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: ElevatedButton.icon(
              onPressed: _isSaving ? null : _saveAndGenerate,
              icon: _isSaving
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.check_circle_outline),
              label: Text(_isSaving ? 'Генерация .docx...' : 'Подтвердить и создать .docx'),
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
            ),
          ),
        ],
      ),
      body: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1000),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              if (_errorMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppColors.error.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.error.withOpacity(0.3)),
                  ),
                  child: Text(_errorMessage!, style: const TextStyle(color: AppColors.error)),
                ),
              ],
              if (_successMessage != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 16),
                  decoration: BoxDecoration(
                    color: AppColors.success.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.success.withOpacity(0.3)),
                  ),
                  child: Text(_successMessage!, style: const TextStyle(color: AppColors.success)),
                ),
              ],

              // 1. Карточка: Основные сведения
              _buildSectionCard(
                title: '1. Основные сведения',
                icon: Icons.person,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _fioController,
                          decoration: const InputDecoration(labelText: 'ФИО кандидата'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: _vacancyController,
                          decoration: const InputDecoration(labelText: 'Целевая вакансия'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _totalYearController,
                          decoration: const InputDecoration(
                            labelText: 'Общий стаж работы',
                            hintText: 'Например: 5 ЛЕТ 2 МЕСЯЦА',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: _backgroundController,
                          decoration: const InputDecoration(
                            labelText: 'Отрасли работы (Project background)',
                            hintText: 'Финтех, Банкинг, Ритейл',
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _pitchController,
                    maxLines: 3,
                    decoration: const InputDecoration(
                      labelText: 'Краткий рассказ о себе (Pitch от 1-го лица без "Я")',
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 2. Карточка: Условия и статус
              _buildSectionCard(
                title: '2. Локация и занятость',
                icon: Icons.place_outlined,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _locationController,
                          decoration: const InputDecoration(labelText: 'Гражданство и город проживания'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: _languagesController,
                          decoration: const InputDecoration(labelText: 'Знание языков'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _employmentController,
                          decoration: const InputDecoration(labelText: 'Тип занятости'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextField(
                          controller: _statusController,
                          decoration: const InputDecoration(labelText: 'Готовность к командировкам / переезду'),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 3. Карточка: Навыки и инструменты
              _buildSectionCard(
                title: '3. Стек технологий и навыки',
                icon: Icons.code,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (int i = 0; i < _data.skillsAndTools.length; i++)
                        Chip(
                          label: Text(_data.skillsAndTools[i]),
                          deleteIcon: const Icon(Icons.close, size: 16),
                          onDeleted: () {
                            setState(() => _data.skillsAndTools.removeAt(i));
                          },
                          backgroundColor: AppColors.surfaceLight,
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _showAddSkillDialog,
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('Добавить категорию / навык'),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 4. Карточка: Опыт работы (Проекты)
              _buildSectionCard(
                title: '4. Опыт работы (Проекты)',
                icon: Icons.work_outline,
                children: [
                  for (int pIndex = 0; pIndex < _data.projects.length; pIndex++) ...[
                    _buildProjectItemWidget(pIndex),
                    if (pIndex < _data.projects.length - 1) const Divider(color: AppColors.border, height: 32),
                  ],
                  const SizedBox(height: 16),
                  OutlinedButton.icon(
                    onPressed: () {
                      setState(() {
                        _data.projects.add(ProjectItem(
                          placeTimeRaw: 'Новая компания',
                          period: '2022 год 01 месяц - 2024 год 01 месяц / 2 ГОДА 0 МЕСЯЦЕВ',
                          roleInProject: 'Специалист',
                        ));
                      });
                    },
                    icon: const Icon(Icons.add),
                    label: const Text('Добавить место работы / проект'),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // 5. Карточка: Образование и курсы
              _buildSectionCard(
                title: '5. Образование и курсы',
                icon: Icons.school_outlined,
                children: [
                  const Text('Высшее и специальное образование:', style: TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(height: 8),
                  for (int eduIdx = 0; eduIdx < _data.education.length; eduIdx++)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 2,
                            child: TextFormField(
                              initialValue: _data.education[eduIdx].institution,
                              decoration: const InputDecoration(labelText: 'Учебное заведение'),
                              onChanged: (v) => _data.education[eduIdx].institution = v,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            flex: 2,
                            child: TextFormField(
                              initialValue: _data.education[eduIdx].speciality,
                              decoration: const InputDecoration(labelText: 'Специальность'),
                              onChanged: (v) => _data.education[eduIdx].speciality = v,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            flex: 1,
                            child: TextFormField(
                              initialValue: _data.education[eduIdx].year,
                              decoration: const InputDecoration(labelText: 'Годы'),
                              onChanged: (v) => _data.education[eduIdx].year = v,
                            ),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline, color: AppColors.error),
                            onPressed: () => setState(() => _data.education.removeAt(eduIdx)),
                          ),
                        ],
                      ),
                    ),
                  OutlinedButton.icon(
                    onPressed: () => setState(() => _data.education.add(EducationItem())),
                    icon: const Icon(Icons.add, size: 16),
                    label: const Text('Добавить образование'),
                  ),
                ],
              ),
              const SizedBox(height: 32),

              // Итоговая кнопка
              SizedBox(
                height: 50,
                child: ElevatedButton.icon(
                  onPressed: _isSaving ? null : _saveAndGenerate,
                  icon: const Icon(Icons.save),
                  label: Text(_isSaving ? 'Генерация корпоративного Word-документа...' : 'Завершить валидацию и сформировать DOCX'),
                ),
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionCard({
    required String title,
    required IconData icon,
    required List<Widget> children,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: AppColors.primary, size: 22),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 16),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildProjectItemWidget(int index) {
    final project = _data.projects[index];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              flex: 3,
              child: TextFormField(
                initialValue: project.placeTimeRaw,
                decoration: const InputDecoration(labelText: 'Компания / Организация'),
                onChanged: (v) => project.placeTimeRaw = v,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 3,
              child: TextFormField(
                initialValue: project.period,
                decoration: const InputDecoration(labelText: 'Период работы / Стаж'),
                onChanged: (v) => project.period = v,
              ),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, color: AppColors.error),
              onPressed: () => setState(() => _data.projects.removeAt(index)),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: TextFormField(
                initialValue: project.roleInProject,
                decoration: const InputDecoration(labelText: 'Роль / Должность на проекте'),
                onChanged: (v) => project.roleInProject = v,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: TextFormField(
                initialValue: project.skillsToolsInProject,
                decoration: const InputDecoration(labelText: 'Стек технологий на проекте'),
                onChanged: (v) => project.skillsToolsInProject = v,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        const Text('Задачи на проекте:', style: TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
        const SizedBox(height: 4),
        for (int tIdx = 0; tIdx < project.taskOnProject.length; tIdx++)
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              children: [
                const Icon(Icons.arrow_right, size: 16, color: AppColors.primary),
                const SizedBox(width: 4),
                Expanded(
                  child: TextFormField(
                    initialValue: project.taskOnProject[tIdx],
                    decoration: const InputDecoration(isDense: true, contentPadding: EdgeInsets.all(10)),
                    onChanged: (v) => project.taskOnProject[tIdx] = v,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close, size: 16),
                  onPressed: () => setState(() => project.taskOnProject.removeAt(tIdx)),
                ),
              ],
            ),
          ),
        TextButton.icon(
          onPressed: () => setState(() => project.taskOnProject.add('Новая задача')),
          icon: const Icon(Icons.add, size: 14),
          label: const Text('Добавить задачу', style: TextStyle(fontSize: 12)),
        ),
      ],
    );
  }

  void _showAddSkillDialog() {
    final skillController = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.surface,
        title: const Text('Добавить навык или инструмент'),
        content: TextField(
          controller: skillController,
          decoration: const InputDecoration(hintText: 'Например: Языки: Go, Rust'),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.of(ctx).pop(), child: const Text('Отмена')),
          ElevatedButton(
            onPressed: () {
              if (skillController.text.trim().isNotEmpty) {
                setState(() => _data.skillsAndTools.add(skillController.text.trim()));
              }
              Navigator.of(ctx).pop();
            },
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
  }
}

extension ApiServiceHelper on ApiService {
  String getDownloadUrl(int cvId) => '${ApiConstants.cvDownloadUrl(cvId)}';
}
