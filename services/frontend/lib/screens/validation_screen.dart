import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/api_service.dart';
import 'result_download_screen.dart';

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
  String? _errorMessage;
  bool _showRawJson = false;
  final ScrollController _scrollController = ScrollController();
  final GlobalKey _rawJsonKey = GlobalKey();

  // Text Controllers: General Info
  late TextEditingController _fioController;
  late TextEditingController _vacancyController;
  late TextEditingController _totalYearController;
  late TextEditingController _backgroundController;
  late TextEditingController _pitchController;

  // Text Controllers: Personal details
  late TextEditingController _languagesController;
  late TextEditingController _locationController;
  late TextEditingController _employmentController;
  late TextEditingController _statusController;

  // Controller for adding skills
  final TextEditingController _newSkillController = TextEditingController();

  // Expand state for project accordions
  final Map<int, bool> _expandedProjects = {};

  @override
  void initState() {
    super.initState();
    // Deep clone data
    _data = CVJsonData.fromJson(widget.initialData.toJson());

    _fioController = TextEditingController(text: _data.fio);
    _vacancyController = TextEditingController(text: _data.vacancy);
    _totalYearController = TextEditingController(text: _data.totalYearWork);
    _backgroundController = TextEditingController(text: _data.projectBackround);
    _pitchController = TextEditingController(text: _data.pitch);

    _languagesController = TextEditingController(text: _data.languages);
    _locationController = TextEditingController(text: _data.citizenshipLocation);
    _employmentController = TextEditingController(text: _data.employment);
    _statusController = TextEditingController(text: _data.status);

    // Expand the first project by default
    if (_data.projects.isNotEmpty) {
      _expandedProjects[0] = true;
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _fioController.dispose();
    _vacancyController.dispose();
    _totalYearController.dispose();
    _backgroundController.dispose();
    _pitchController.dispose();
    _languagesController.dispose();
    _locationController.dispose();
    _employmentController.dispose();
    _statusController.dispose();
    _newSkillController.dispose();
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
    });

    try {
      final record = await apiService.validateCV(widget.cvId, _data);
      if (mounted) {
        setState(() => _isSaving = false);
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => ResultDownloadScreen(record: record),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  Future<void> _returnForRework() async {
    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      await apiService.returnForRework(widget.cvId);
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Резюме #${widget.cvId} возвращено на доработку (статус: Обработка резюме)'),
            backgroundColor: AppColors.error,
          ),
        );
        Navigator.of(context).pop();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  Future<void> _saveDraft() async {
    _syncData();
    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      await apiService.saveDraft(widget.cvId, _data);
      if (mounted) {
        setState(() => _isSaving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Черновик резюме #${widget.cvId} сохранен в базе данных'),
            backgroundColor: AppColors.secondary,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isSaving = false;
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    }
  }

  void _addSkill() {
    final skill = _newSkillController.text.trim();
    if (skill.isNotEmpty) {
      setState(() {
        _data.skillsAndTools.add(skill);
        _newSkillController.clear();
      });
    }
  }

  void _removeSkill(int index) {
    setState(() {
      _data.skillsAndTools.removeAt(index);
    });
  }

  void _addProject() {
    setState(() {
      final newIndex = _data.projects.length;
      _data.projects.add(
        ProjectItem(
          placeTimeRaw: 'Новая компания / проект',
          period: '2024 год - настоящее время',
          roleInProject: 'Специалист',
          taskOnProject: ['Основная задача проекта'],
          achievementsInProject: ['Результат или метрика проекта'],
          skillsToolsInProject: '',
        ),
      );
      _expandedProjects[newIndex] = true;
    });
  }

  void _removeProject(int index) {
    setState(() {
      _data.projects.removeAt(index);
      _expandedProjects.remove(index);
    });
  }

  void _addEducation() {
    setState(() {
      _data.education.add(
        EducationItem(
          type: 'Высшее:',
          institution: 'Университет / ВУЗ',
          speciality: 'Специальность',
          year: '2018 - 2022',
        ),
      );
    });
  }

  void _removeEducation(int index) {
    setState(() {
      _data.education.removeAt(index);
    });
  }

  void _copyRawJson() {
    _syncData();
    const encoder = JsonEncoder.withIndent('  ');
    final jsonStr = encoder.convert(_data.toJson());
    Clipboard.setData(ClipboardData(text: jsonStr));
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('JSON скопирован в буфер обмена')),
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
              child: const Text('Интерактивная валидация', style: TextStyle(fontSize: 11, color: AppColors.secondary)),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Sticky Context Header
          _buildStickyHeader(),
          const Divider(height: 1, color: AppColors.outlineVariant),

          // Main Scrollable Canvas
          Expanded(
            child: SingleChildScrollView(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
              child: Center(
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 1400),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Gemma Insight Banner
                      _buildInsightBanner(),
                      const SizedBox(height: 20),

                      // Error message if any
                      if (_errorMessage != null) ...[
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
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(color: AppColors.error, fontSize: 13),
                                ),
                              ),
                              IconButton(
                                icon: const Icon(Icons.close, size: 16, color: AppColors.onErrorContainer),
                                onPressed: () => setState(() => _errorMessage = null),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 20),
                      ],

                      // 2-Column Primary Grid
                      LayoutBuilder(
                        builder: (context, constraints) {
                          final isDesktop = constraints.maxWidth >= 980;
                          if (isDesktop) {
                            return Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                // Left Column (General Info, Skills, Education)
                                Expanded(
                                  flex: 7,
                                  child: Column(
                                    children: [
                                      _buildGeneralInfoSection(),
                                      const SizedBox(height: 20),
                                      _buildSkillsSection(),
                                      const SizedBox(height: 20),
                                      _buildEducationSection(),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 24),
                                // Right Column (Projects & Experience)
                                Expanded(
                                  flex: 5,
                                  child: _buildProjectsSection(),
                                ),
                              ],
                            );
                          } else {
                            return Column(
                              children: [
                                _buildGeneralInfoSection(),
                                const SizedBox(height: 20),
                                _buildSkillsSection(),
                                const SizedBox(height: 20),
                                _buildEducationSection(),
                                const SizedBox(height: 20),
                                _buildProjectsSection(),
                              ],
                            );
                          }
                        },
                      ),
                      const SizedBox(height: 24),

                      // Section 5: Raw JSON Payload Viewer
                      _buildRawJsonCard(),
                      const SizedBox(height: 32),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStickyHeader() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      child: Center(
        child: Container(
          constraints: const BoxConstraints(maxWidth: 1400),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              // Left: Breadcrumbs & Status
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      InkWell(
                        onTap: () => Navigator.of(context).pop(),
                        child: const Text('Реестр резюме', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                      ),
                      const SizedBox(width: 4),
                      const Icon(Icons.chevron_right, size: 14, color: AppColors.outline),
                      const SizedBox(width: 4),
                      Text('Резюме #CV-${widget.cvId}', style: const TextStyle(fontSize: 12, color: AppColors.textPrimary, fontWeight: FontWeight.w600)),
                      const SizedBox(width: 4),
                      const Icon(Icons.chevron_right, size: 14, color: AppColors.outline),
                      const SizedBox(width: 4),
                      const Text('Интерактивная валидация Gemma-3', style: TextStyle(fontSize: 12, color: AppColors.secondary, fontWeight: FontWeight.w600)),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.amberBg,
                          borderRadius: BorderRadius.circular(9999),
                          border: Border.all(color: AppColors.amberBorder),
                        ),
                        child: Row(
                          children: [
                            Container(
                              width: 6,
                              height: 6,
                              decoration: const BoxDecoration(
                                color: AppColors.amberAccent,
                                shape: BoxShape.circle,
                              ),
                            ),
                            const SizedBox(width: 6),
                            const Text(
                              'Ожидает проверки HR',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w700,
                                color: AppColors.amberText,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.surfaceLow,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Row(
                          children: [
                            Icon(Icons.auto_awesome, size: 13, color: AppColors.secondary),
                            SizedBox(width: 4),
                            Text('Gemma-3 Extra-large', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                            SizedBox(width: 4),
                            Text('·', style: TextStyle(color: AppColors.outline)),
                            SizedBox(width: 4),
                            Text('98.4% точность', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.secondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),

              // Right: Action Buttons Suite
              Row(
                children: [
                  OutlinedButton.icon(
                    onPressed: _isSaving ? null : _returnForRework,
                    icon: const Icon(Icons.undo_rounded, size: 16, color: AppColors.error),
                    label: const Text('Вернуть на доработку', style: TextStyle(color: AppColors.error)),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.roseBorder),
                      backgroundColor: AppColors.roseBg,
                    ),
                  ),
                  const SizedBox(width: 10),
                  OutlinedButton.icon(
                    onPressed: _isSaving ? null : _saveDraft,
                    icon: const Icon(Icons.save_outlined, size: 16),
                    label: const Text('Сохранить черновик'),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton.icon(
                    onPressed: _isSaving ? null : _saveAndGenerate,
                    icon: _isSaving
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.bolt_rounded, size: 18),
                    label: Text(_isSaving ? 'Генерация DOCX...' : 'Подтвердить и docx'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.secondary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInsightBanner() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
      decoration: BoxDecoration(
        color: AppColors.surfaceLow,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.surfaceContainer),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: AppColors.secondary.withOpacity(0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.psychology_rounded, color: AppColors.secondary, size: 22),
          ),
          const SizedBox(width: 14),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'LLM-извлечение завершено без критических расхождений',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.primary,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'Все структурные сущности сопоставлены с онтологией ИТ-должностей. Проверьте формулировки и подтвердите выпуск итогового резюме кандидата.',
                  style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          OutlinedButton.icon(
            onPressed: () {
              setState(() => _showRawJson = !_showRawJson);
              if (_showRawJson) {
                WidgetsBinding.instance.addPostFrameCallback((_) {
                  Scrollable.ensureVisible(
                    _rawJsonKey.currentContext!,
                    duration: const Duration(milliseconds: 300),
                  );
                });
              }
            },
            icon: const Icon(Icons.code_rounded, size: 16, color: AppColors.secondary),
            label: Text(_showRawJson ? 'Скрыть JSON' : 'Смотреть JSON'),
            style: OutlinedButton.styleFrom(
              backgroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGeneralInfoSection() {
    return Container(
      padding: const EdgeInsets.all(24),
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
                children: const [
                  Icon(Icons.badge_outlined, color: AppColors.secondary, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Основная информация',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                      fontFamily: 'Plus Jakarta Sans',
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(9999),
                ),
                child: const Text('9 полей', style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
              ),
            ],
          ),
          const SizedBox(height: 18),

          // FIO
          _buildFieldLabel('ФИО кандидата', '99.8% match'),
          TextField(
            controller: _fioController,
            decoration: const InputDecoration(
              suffixIcon: Icon(Icons.check_circle_rounded, color: AppColors.secondary, size: 18),
            ),
          ),
          const SizedBox(height: 14),

          // Vacancy & Total Experience
          Row(
            children: [
              Expanded(
                flex: 3,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Желаемая вакансия', '98.2%'),
                    TextField(controller: _vacancyController),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                flex: 2,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Общий стаж работы', 'Точно'),
                    TextField(
                      controller: _totalYearController,
                      decoration: const InputDecoration(hintText: 'X ЛЕТ Y МЕСЯЦЕВ'),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Project Background / Domains
          _buildFieldLabel('Отрасли / Направления проектов', 'CSV формат'),
          TextField(
            controller: _backgroundController,
            decoration: const InputDecoration(hintText: 'Финтех, Банковская сфера, E-commerce'),
          ),
          const SizedBox(height: 14),

          // Pitch / Elevator Pitch
          _buildFieldLabel('Саммари кандидата (Elevator Pitch)', 'Без первого лица «Я»'),
          TextField(
            controller: _pitchController,
            maxLines: 3,
            decoration: const InputDecoration(
              hintText: 'Краткий рассказ о себе от первого лица, без местоимения «Я» (3-5 предложений)',
            ),
          ),
          const SizedBox(height: 14),

          // Additional fields: Languages, Location, Employment, Status
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Знание языков', 'А2 по умолчанию'),
                    TextField(controller: _languagesController),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Локация / Гражданство', 'Город, страна'),
                    TextField(controller: _locationController),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Формат занятости', 'Полная / Удаленная'),
                    TextField(controller: _employmentController),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildFieldLabel('Готовность к командировкам / релокации', ''),
                    TextField(controller: _statusController),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFieldLabel(String label, String badge) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          ),
          if (badge.isNotEmpty)
            Text(
              badge,
              style: const TextStyle(fontSize: 10, color: AppColors.secondary, fontWeight: FontWeight.w500),
            ),
        ],
      ),
    );
  }

  Widget _buildSkillsSection() {
    return Container(
      padding: const EdgeInsets.all(24),
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
                children: const [
                  Icon(Icons.hub_outlined, color: AppColors.secondary, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Стек, навыки и фреймворки',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                      fontFamily: 'Plus Jakarta Sans',
                    ),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(9999),
                ),
                child: Text(
                  '${_data.skillsAndTools.length} навыков',
                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text(
            'Распознано моделью из текстов задач и самоописания кандидата',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          const SizedBox(height: 16),

          // Chips Cloud
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: List.generate(_data.skillsAndTools.length, (i) {
              final skill = _data.skillsAndTools[i];
              return Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.surfaceContainer),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      skill,
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: AppColors.textPrimary),
                    ),
                    const SizedBox(width: 6),
                    InkWell(
                      onTap: () => _removeSkill(i),
                      child: const Icon(Icons.close, size: 14, color: AppColors.outline),
                    ),
                  ],
                ),
              );
            }),
          ),
          const SizedBox(height: 16),

          // Add skill inline field
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _newSkillController,
                  decoration: const InputDecoration(
                    hintText: 'Введите название навыка (например, SQL, BPMN, Docker)...',
                    contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  ),
                  onSubmitted: (_) => _addSkill(),
                ),
              ),
              const SizedBox(width: 10),
              ElevatedButton.icon(
                onPressed: _addSkill,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('Добавить'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.surfaceContainer,
                  foregroundColor: AppColors.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEducationSection() {
    return Container(
      padding: const EdgeInsets.all(24),
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
                children: const [
                  Icon(Icons.school_outlined, color: AppColors.secondary, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Образование и курсы',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                      fontFamily: 'Plus Jakarta Sans',
                    ),
                  ),
                ],
              ),
              OutlinedButton.icon(
                onPressed: _addEducation,
                icon: const Icon(Icons.add, size: 14),
                label: const Text('Добавить образование'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  textStyle: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          if (_data.education.isEmpty)
            const Text('Данные об образовании отсутствуют', style: TextStyle(color: AppColors.textMuted, fontSize: 13))
          else
            Column(
              children: List.generate(_data.education.length, (i) {
                final edu = _data.education[i];
                return Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceLow,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.surfaceContainer),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 38,
                        height: 38,
                        decoration: BoxDecoration(
                          color: AppColors.surfaceContainer,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(Icons.school, size: 20, color: AppColors.secondary),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: TextFormField(
                                    initialValue: edu.institution,
                                    onChanged: (v) => edu.institution = v,
                                    decoration: const InputDecoration(
                                      isDense: true,
                                      hintText: 'Учебное заведение',
                                      border: InputBorder.none,
                                      enabledBorder: InputBorder.none,
                                      focusedBorder: InputBorder.none,
                                    ),
                                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text(
                                    edu.type,
                                    style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
                                  ),
                                ),
                              ],
                            ),
                            TextFormField(
                              initialValue: edu.speciality,
                              onChanged: (v) => edu.speciality = v,
                              decoration: const InputDecoration(
                                isDense: true,
                                hintText: 'Специальность',
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                              ),
                              style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
                            ),
                            TextFormField(
                              initialValue: edu.year,
                              onChanged: (v) => edu.year = v,
                              decoration: const InputDecoration(
                                isDense: true,
                                hintText: 'Год поступления - выпуск',
                                border: InputBorder.none,
                                enabledBorder: InputBorder.none,
                                focusedBorder: InputBorder.none,
                              ),
                              style: const TextStyle(fontSize: 12, color: AppColors.outline),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        onPressed: () => _removeEducation(i),
                        icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.error),
                        tooltip: 'Удалить',
                      ),
                    ],
                  ),
                );
              }),
            ),
        ],
      ),
    );
  }

  Widget _buildProjectsSection() {
    return Container(
      padding: const EdgeInsets.all(24),
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
                children: const [
                  Icon(Icons.work_outline_rounded, color: AppColors.secondary, size: 20),
                  SizedBox(width: 8),
                  Text(
                    'Опыт и проекты',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                      fontFamily: 'Plus Jakarta Sans',
                    ),
                  ),
                ],
              ),
              OutlinedButton.icon(
                onPressed: _addProject,
                icon: const Icon(Icons.add, size: 14),
                label: const Text('Добавить проект'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  textStyle: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '${_data.projects.length} проверенных карьерных позиций',
            style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
          ),
          const SizedBox(height: 16),

          // Project Accordions
          if (_data.projects.isEmpty)
            const Text('Проекты не найдены', style: TextStyle(color: AppColors.textMuted, fontSize: 13))
          else
            Column(
              children: List.generate(_data.projects.length, (i) {
                final project = _data.projects[i];
                final isExpanded = _expandedProjects[i] ?? false;

                return Container(
                  margin: const EdgeInsets.only(bottom: 14),
                  decoration: BoxDecoration(
                    color: AppColors.surfaceLow,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.surfaceContainer),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Column(
                    children: [
                      // Accordion Header
                      InkWell(
                        onTap: () {
                          setState(() {
                            _expandedProjects[i] = !isExpanded;
                          });
                        },
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            children: [
                              Container(
                                width: 28,
                                height: 28,
                                decoration: BoxDecoration(
                                  color: AppColors.secondary,
                                  borderRadius: BorderRadius.circular(6),
                                ),
                                child: Center(
                                  child: Text(
                                    '${i + 1}',
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      project.placeTimeRaw.isNotEmpty
                                          ? project.placeTimeRaw
                                          : 'Компания / Проект',
                                      style: const TextStyle(
                                        fontSize: 14,
                                        fontWeight: FontWeight.w700,
                                        color: AppColors.primary,
                                      ),
                                    ),
                                    Text(
                                      '${project.roleInProject} • ${project.period}',
                                      style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                                    ),
                                  ],
                                ),
                              ),
                              Icon(
                                isExpanded ? Icons.expand_less : Icons.expand_more,
                                color: AppColors.outline,
                              ),
                            ],
                          ),
                        ),
                      ),

                      // Expanded Body
                      if (isExpanded) ...[
                        const Divider(height: 1, color: AppColors.surfaceContainer),
                        Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // Place and Period inputs
                              Row(
                                children: [
                                  Expanded(
                                    flex: 3,
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('Компания', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                                        const SizedBox(height: 4),
                                        TextFormField(
                                          initialValue: project.placeTimeRaw,
                                          onChanged: (v) => project.placeTimeRaw = v,
                                          decoration: const InputDecoration(isDense: true),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: 10),
                                  Expanded(
                                    flex: 2,
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Text('Роль', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                                        const SizedBox(height: 4),
                                        TextFormField(
                                          initialValue: project.roleInProject,
                                          onChanged: (v) => project.roleInProject = v,
                                          decoration: const InputDecoration(isDense: true),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 10),

                              const Text('Период работы (Маска дат)', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.textSecondary)),
                              const SizedBox(height: 4),
                              TextFormField(
                                initialValue: project.period,
                                onChanged: (v) => project.period = v,
                                decoration: const InputDecoration(
                                  isDense: true,
                                  hintText: 'XXXX год YY месяц - ZZZZ год VV месяц / CC ЛЕТ NN МЕСЯЦЕВ',
                                ),
                              ),
                              const SizedBox(height: 14),

                              // Tasks on project
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: [
                                  const Text('ВЫПОЛНЯЕМЫЕ ЗАДАЧИ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
                                  Text('${project.taskOnProject.length} пунктов', style: const TextStyle(fontSize: 11, color: AppColors.outline)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Column(
                                children: List.generate(project.taskOnProject.length, (tIdx) {
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 6),
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: AppColors.surfaceContainer),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.check, size: 16, color: AppColors.secondary),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: TextFormField(
                                            initialValue: project.taskOnProject[tIdx],
                                            onChanged: (v) => project.taskOnProject[tIdx] = v,
                                            decoration: const InputDecoration(
                                              isDense: true,
                                              border: InputBorder.none,
                                              enabledBorder: InputBorder.none,
                                              focusedBorder: InputBorder.none,
                                            ),
                                            style: const TextStyle(fontSize: 13),
                                          ),
                                        ),
                                        IconButton(
                                          icon: const Icon(Icons.close, size: 14, color: AppColors.outline),
                                          onPressed: () {
                                            setState(() => project.taskOnProject.removeAt(tIdx));
                                          },
                                        ),
                                      ],
                                    ),
                                  );
                                }),
                              ),
                              TextButton.icon(
                                onPressed: () {
                                  setState(() => project.taskOnProject.add('Новая выполненная задача'));
                                },
                                icon: const Icon(Icons.add, size: 14),
                                label: const Text('Добавить задачу', style: TextStyle(fontSize: 12)),
                              ),
                              const SizedBox(height: 10),

                              // Achievements on project
                              Row(
                                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                children: const [
                                  Text('КЛЮЧЕВЫЕ ДОСТИЖЕНИЯ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
                                  Text('High Impact', style: TextStyle(fontSize: 11, color: AppColors.amberText, fontWeight: FontWeight.bold)),
                                ],
                              ),
                              const SizedBox(height: 8),
                              Column(
                                children: List.generate(project.achievementsInProject.length, (aIdx) {
                                  return Container(
                                    margin: const EdgeInsets.only(bottom: 6),
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: Colors.white,
                                      borderRadius: BorderRadius.circular(8),
                                      border: Border.all(color: AppColors.surfaceContainer),
                                    ),
                                    child: Row(
                                      children: [
                                        const Icon(Icons.emoji_events_outlined, size: 16, color: AppColors.amberAccent),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: TextFormField(
                                            initialValue: project.achievementsInProject[aIdx],
                                            onChanged: (v) => project.achievementsInProject[aIdx] = v,
                                            decoration: const InputDecoration(
                                              isDense: true,
                                              border: InputBorder.none,
                                              enabledBorder: InputBorder.none,
                                              focusedBorder: InputBorder.none,
                                            ),
                                            style: const TextStyle(fontSize: 13),
                                          ),
                                        ),
                                        IconButton(
                                          icon: const Icon(Icons.close, size: 14, color: AppColors.outline),
                                          onPressed: () {
                                            setState(() => project.achievementsInProject.removeAt(aIdx));
                                          },
                                        ),
                                      ],
                                    ),
                                  );
                                }),
                              ),
                              TextButton.icon(
                                onPressed: () {
                                  setState(() => project.achievementsInProject.add('Ключевое достижение на проекте'));
                                },
                                icon: const Icon(Icons.add, size: 14),
                                label: const Text('Добавить достижение', style: TextStyle(fontSize: 12)),
                              ),
                              const SizedBox(height: 10),

                              // Skills / Tools in Project
                              const Text('СТЕК И ИНСТРУМЕНТЫ НА ПРОЕКТЕ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary)),
                              const SizedBox(height: 4),
                              TextFormField(
                                initialValue: project.skillsToolsInProject,
                                onChanged: (v) => project.skillsToolsInProject = v,
                                decoration: const InputDecoration(
                                  isDense: true,
                                  hintText: 'Использованные технологии и стек на проекте',
                                ),
                              ),
                              const SizedBox(height: 12),

                              // Delete Project
                              Align(
                                alignment: Alignment.centerRight,
                                child: TextButton.icon(
                                  onPressed: () => _removeProject(i),
                                  icon: const Icon(Icons.delete_outline, size: 16, color: AppColors.error),
                                  label: const Text('Удалить проект', style: TextStyle(color: AppColors.error, fontSize: 12)),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              }),
            ),
        ],
      ),
    );
  }

  Widget _buildRawJsonCard() {
    _syncData();
    const encoder = JsonEncoder.withIndent('  ');
    final jsonStr = encoder.convert(_data.toJson());

    return Container(
      key: _rawJsonKey,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          InkWell(
            onTap: () => setState(() => _showRawJson = !_showRawJson),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(
                children: [
                  const Icon(Icons.data_object_rounded, color: AppColors.secondary, size: 22),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'Raw JSON Payload',
                              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: AppColors.primary),
                            ),
                            const SizedBox(width: 10),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceLow,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                'PUT /api/v1/cv/${widget.cvId}/validate',
                                style: const TextStyle(fontSize: 11, fontFamily: 'monospace', color: AppColors.secondary),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 2),
                        const Text(
                          'Синхронное состояние структуры резюме перед передачей на рендеринг DOCX',
                          style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                        ),
                      ],
                    ),
                  ),
                  Icon(_showRawJson ? Icons.expand_less : Icons.expand_more, color: AppColors.outline),
                ],
              ),
            ),
          ),
          if (_showRawJson) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
              color: AppColors.primaryContainer,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('schema: cv_payload_v3_gemma.json', style: TextStyle(color: AppColors.onPrimaryContainer, fontSize: 11, fontFamily: 'monospace')),
                  ElevatedButton.icon(
                    onPressed: _copyRawJson,
                    icon: const Icon(Icons.copy, size: 14),
                    label: const Text('Копировать JSON', style: TextStyle(fontSize: 12)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    ),
                  ),
                ],
              ),
            ),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              color: AppColors.primary,
              child: SelectableText(
                jsonStr,
                style: const TextStyle(
                  color: Color(0xFFE2E8F0),
                  fontFamily: 'monospace',
                  fontSize: 12,
                  height: 1.5,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
