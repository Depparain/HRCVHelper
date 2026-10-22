import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants/app_theme.dart';
import '../models/cv_model.dart';
import '../services/auth_provider.dart';
import '../services/api_service.dart';
import '../widgets/upload_cv_dialog.dart';
import 'login_screen.dart';
import 'validation_screen.dart';
import 'result_download_screen.dart';
import 'admin_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<CVRecord> _allCVs = [];
  bool _isLoading = false;
  String _selectedFilterTab = 'Все'; // 'Все', 'Загружено', 'Ожидает проверки HR', 'Готово', 'Ошибка парсинга'
  String _searchQuery = '';
  String _selectedRoleFilter = 'all';
  String _sortOrder = 'newest';

  @override
  void initState() {
    super.initState();
    _loadCVs();
  }

  Future<void> _loadCVs() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    setState(() => _isLoading = true);

    try {
      final cvs = await apiService.listCVs(hrId: auth.currentUser?.hrId);
      if (mounted) {
        setState(() {
          _allCVs = cvs;
          _isLoading = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _openUploadModal() async {
    final auth = Provider.of<AuthProvider>(context, listen: false);
    final hrId = auth.currentUser?.hrId ?? 1;

    final record = await showDialog<CVRecord>(
      context: context,
      barrierDismissible: false,
      builder: (_) => UploadCVDialog(hrId: hrId),
    );

    if (record != null && mounted) {
      await _loadCVs();
      // Navigate to validation screen
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ValidationScreen(
            cvId: record.cvId,
            initialData: record.jsonData,
          ),
        ),
      ).then((_) => _loadCVs());
    }
  }

  List<CVRecord> get _filteredCVs {
    return _allCVs.where((cv) {
      // Tab filter
      if (_selectedFilterTab == 'Загружено' && cv.status != 'Загружено') return false;
      if (_selectedFilterTab == 'Ожидает проверки HR' && cv.status != 'Ожидает проверки HR') return false;
      if (_selectedFilterTab == 'Готово' && cv.status != 'Готово') return false;
      if (_selectedFilterTab == 'Ошибка парсинга' && !cv.status.contains('Ошибк')) return false;

      // Search query
      if (_searchQuery.isNotEmpty) {
        final q = _searchQuery.toLowerCase();
        final fioMatch = cv.jsonData.fio.toLowerCase().contains(q);
        final vacMatch = cv.jsonData.vacancy.toLowerCase().contains(q);
        final skillMatch = cv.jsonData.skillsAndTools.any((s) => s.toLowerCase().contains(q));
        if (!fioMatch && !vacMatch && !skillMatch) return false;
      }

      // Role filter
      if (_selectedRoleFilter != 'all') {
        final vac = cv.jsonData.vacancy.toLowerCase();
        if (_selectedRoleFilter == 'lead' && !vac.contains('lead') && !vac.contains('руковод')) return false;
        if (_selectedRoleFilter == 'senior' && !vac.contains('senior') && !vac.contains('старш')) return false;
        if (_selectedRoleFilter == 'analyst' && !vac.contains('аналитик') && !vac.contains('analyst')) return false;
        if (_selectedRoleFilter == 'ds' && !vac.contains('data') && !vac.contains('ml') && !vac.contains('ai')) return false;
      }

      return true;
    }).toList();
  }

  int get _countPendingValidation =>
      _allCVs.where((c) => c.status == 'Ожидает проверки HR').length;

  int get _countReady =>
      _allCVs.where((c) => c.status == 'Готово').length;

  int get _countUploaded =>
      _allCVs.where((c) => c.status == 'Загружено' || c.status.contains('Обработ') || c.status.contains('Конверт')).length;

  int get _countErrors =>
      _allCVs.where((c) => c.status.contains('Ошибк')).length;

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final user = auth.currentUser;
    final userName = user?.fullName.isNotEmpty == true ? user!.fullName : 'Елена Смирнова';

    return Scaffold(
      backgroundColor: AppColors.background,
      body: Column(
        children: [
          // 1. Suite Top Navigation Header Bar
          _buildTopSuiteBar(userName, auth),
          const Divider(height: 1, color: AppColors.outlineVariant),

          // 2. Scrollable Dashboard Area
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 24),
              child: Center(
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 1440),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      // Breadcrumb & Live Pipeline Status
                      _buildBreadcrumbAndStatusRow(),
                      const SizedBox(height: 20),

                      // Header Section with Title and CTA
                      _buildHeaderSection(),
                      const SizedBox(height: 24),

                      // 4 Summary Bento Metric Cards
                      _buildBentoMetricsGrid(),
                      const SizedBox(height: 24),

                      // State Machine Filter Tabs Card
                      _buildFilterTabsCard(),
                      const SizedBox(height: 16),

                      // Search & Filter Controls Toolbar
                      _buildSearchAndFiltersToolbar(),
                      const SizedBox(height: 16),

                      // High-Density Data Table Card
                      _buildDataTableCard(),
                      const SizedBox(height: 40),
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

  Widget _buildTopSuiteBar(String userName, AuthProvider auth) {
    return Container(
      height: 64,
      color: Colors.white,
      padding: const EdgeInsets.symmetric(horizontal: 32),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Left: Logo & Module Switcher Tabs
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(Icons.description_rounded, color: AppColors.secondary, size: 20),
              ),
              const SizedBox(width: 10),
              const Text(
                'HRHelper',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppColors.primary,
                  fontFamily: 'Plus Jakarta Sans',
                  letterSpacing: -0.3,
                ),
              ),
              const SizedBox(width: 24),
              Container(width: 1, height: 24, color: AppColors.outlineVariant),
              const SizedBox(width: 24),

              // Module Links
              _buildNavModuleLink('CVHelper', isActive: true),
              const SizedBox(width: 18),
              _buildNavModuleLink('SearchHelper', isActive: false),
              const SizedBox(width: 18),
              _buildNavModuleLink('SuperHR', isActive: false),
              const SizedBox(width: 18),
              InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const AdminScreen()),
                  );
                },
                child: const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    'Контур Админа / Мониторинг',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: AppColors.textMuted,
                    ),
                  ),
                ),
              ),
            ],
          ),

          // Right: Search, Notifications, Settings, Profile
          Row(
            children: [
              // Search shortcut pill
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLow,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.search, size: 16, color: AppColors.textMuted),
                    SizedBox(width: 6),
                    Text('Поиск...', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                    SizedBox(width: 8),
                    Text('⌘K', style: TextStyle(fontSize: 10, color: AppColors.outline, fontWeight: FontWeight.bold)),
                  ],
                ),
              ),
              const SizedBox(width: 14),

              // Notification icon with red badge
              Stack(
                children: [
                  IconButton(
                    icon: const Icon(Icons.notifications_none_rounded, size: 20, color: AppColors.textSecondary),
                    onPressed: () {},
                  ),
                  Positioned(
                    top: 10,
                    right: 10,
                    child: Container(
                      width: 7,
                      height: 7,
                      decoration: const BoxDecoration(
                        color: AppColors.error,
                        shape: BoxShape.circle,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(width: 8),

              // User Profile Chip
              Row(
                children: [
                  CircleAvatar(
                    radius: 16,
                    backgroundColor: AppColors.surfaceContainer,
                    child: Text(
                      userName.isNotEmpty ? userName.substring(0, 1).toUpperCase() : 'Е',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.secondary),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        userName,
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
                      ),
                      const Text(
                        'HR Lead',
                        style: TextStyle(fontSize: 11, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                  const SizedBox(width: 10),
                  IconButton(
                    icon: const Icon(Icons.logout_rounded, size: 18, color: AppColors.textMuted),
                    tooltip: 'Выйти',
                    onPressed: () {
                      auth.logout();
                      Navigator.of(context).pushReplacement(
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildNavModuleLink(String title, {required bool isActive}) {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: isActive ? AppColors.secondary : Colors.transparent,
            width: 2,
          ),
        ),
      ),
      padding: const EdgeInsets.symmetric(vertical: 20),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 13,
          fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
          color: isActive ? AppColors.secondary : AppColors.textMuted,
        ),
      ),
    );
  }

  Widget _buildBreadcrumbAndStatusRow() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            const Text('CVHelper', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.primary)),
            const SizedBox(width: 6),
            const Icon(Icons.chevron_right, size: 14, color: AppColors.outline),
            const SizedBox(width: 6),
            const Text('Реестр резюме', style: TextStyle(fontSize: 12, color: AppColors.textPrimary)),
            const SizedBox(width: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.surfaceContainer,
                borderRadius: BorderRadius.circular(9999),
              ),
              child: const Text(
                'Контур: LLM v3.4 Enterprise',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppColors.secondary),
              ),
            ),
          ],
        ),
        Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(9999),
                border: Border.all(color: AppColors.outlineVariant),
              ),
              child: Row(
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: const BoxDecoration(
                      color: AppColors.emeraldAccent,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                  const Text('Очередь Gemma-3: 2 потока активны', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                ],
              ),
            ),
            const SizedBox(width: 10),
            InkWell(
              onTap: _loadCVs,
              child: Row(
                children: const [
                  Icon(Icons.refresh, size: 14, color: AppColors.textMuted),
                  SizedBox(width: 4),
                  Text('Обновить', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildHeaderSection() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text('РАБОЧИЙ СТОЛ РЕКРУТЕРА', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.8, color: AppColors.secondary)),
            SizedBox(height: 4),
            Text(
              'Реестр резюме',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
                fontFamily: 'Plus Jakarta Sans',
                letterSpacing: -0.5,
              ),
            ),
            SizedBox(height: 4),
            Text(
              'Единая среда структурирования данных кандидатов, верификации LLM-экстракций и генерации стандартизированных профилей',
              style: TextStyle(fontSize: 13, color: AppColors.textMuted),
            ),
          ],
        ),
        Row(
          children: [
            OutlinedButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.tune_rounded, size: 16),
              label: const Text('Правила парсинга'),
            ),
            const SizedBox(width: 12),
            ElevatedButton.icon(
              onPressed: _openUploadModal,
              icon: const Icon(Icons.upload_file_rounded, size: 18),
              label: const Text('+ Загрузить новое резюме'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.secondary,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildBentoMetricsGrid() {
    return Row(
      children: [
        // Metric 1: Total CVs
        Expanded(
          child: _buildBentoCard(
            title: 'Всего резюме',
            value: '${_allCVs.length}',
            badgeText: '+12 за неделю',
            badgeBg: AppColors.emeraldBg,
            badgeColor: AppColors.emeraldText,
            icon: Icons.folder_shared_outlined,
            iconColor: AppColors.secondary,
            iconBg: AppColors.surfaceLow,
          ),
        ),
        const SizedBox(width: 16),

        // Metric 2: Pending HR review
        Expanded(
          child: _buildBentoCard(
            title: 'Ожидают проверки HR',
            value: '$_countPendingValidation',
            badgeText: 'Требуют внимания',
            badgeBg: AppColors.amberBg,
            badgeColor: AppColors.amberText,
            icon: Icons.rate_review_outlined,
            iconColor: AppColors.amberAccent,
            iconBg: AppColors.amberBg,
            isAttention: true,
          ),
        ),
        const SizedBox(width: 16),

        // Metric 3: LLM Processed
        Expanded(
          child: _buildBentoCard(
            title: 'Обработано LLM',
            value: '${_allCVs.length}',
            badgeText: 'Gemma-3 DeepExtract',
            badgeBg: AppColors.purpleBg,
            badgeColor: AppColors.purpleText,
            icon: Icons.psychology_outlined,
            iconColor: AppColors.purpleText,
            iconBg: AppColors.purpleBg,
          ),
        ),
        const SizedBox(width: 16),

        // Metric 4: Exported to DOCX
        Expanded(
          child: _buildBentoCard(
            title: 'Успешно выгружено',
            value: '$_countReady',
            badgeText: 'DOCX • Шаблон Корп',
            badgeBg: AppColors.emeraldBg,
            badgeColor: AppColors.emeraldText,
            icon: Icons.verified_outlined,
            iconColor: AppColors.emeraldText,
            iconBg: AppColors.emeraldBg,
          ),
        ),
      ],
    );
  }

  Widget _buildBentoCard({
    required String title,
    required String value,
    required String badgeText,
    required Color badgeBg,
    required Color badgeColor,
    required IconData icon,
    required Color iconColor,
    required Color iconBg,
    bool isAttention = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isAttention ? AppColors.amberBorder : AppColors.outlineVariant,
          width: isAttention ? 1.5 : 1,
        ),
        boxShadow: const [
          BoxShadow(
            color: Color(0x06091426),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 12, color: AppColors.textMuted, fontWeight: FontWeight.w500)),
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(color: iconBg, borderRadius: BorderRadius.circular(10)),
                child: Icon(icon, color: iconColor, size: 20),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.w700,
              color: isAttention ? AppColors.amberText : AppColors.primary,
              fontFamily: 'Plus Jakarta Sans',
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
            decoration: BoxDecoration(
              color: badgeBg,
              borderRadius: BorderRadius.circular(6),
            ),
            child: Text(
              badgeText,
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: badgeColor),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterTabsCard() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.outlineVariant),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              _buildFilterTabItem('Все', _allCVs.length),
              const SizedBox(width: 6),
              _buildFilterTabItem('Загружено', _countUploaded),
              const SizedBox(width: 6),
              _buildFilterTabItem('Ожидает проверки HR', _countPendingValidation, isAmber: true),
              const SizedBox(width: 6),
              _buildFilterTabItem('Готово', _countReady),
              const SizedBox(width: 6),
              _buildFilterTabItem('Ошибка парсинга', _countErrors),
            ],
          ),
          Row(
            children: [
              OutlinedButton.icon(
                onPressed: () {},
                icon: const Icon(Icons.file_download_outlined, size: 14),
                label: const Text('Экспорт списка', style: TextStyle(fontSize: 12)),
                style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFilterTabItem(String label, int count, {bool isAmber = false}) {
    final isSelected = _selectedFilterTab == label;

    return InkWell(
      onTap: () => setState(() => _selectedFilterTab = label),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected
              ? (isAmber ? AppColors.amberBg : AppColors.primary)
              : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: isSelected && isAmber ? Border.all(color: AppColors.amberBorder) : null,
        ),
        child: Row(
          children: [
            if (isAmber) ...[
              Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                  color: AppColors.amberAccent,
                  shape: BoxShape.circle,
                ),
              ),
              const SizedBox(width: 6),
            ],
            Text(
              label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                color: isSelected
                    ? (isAmber ? AppColors.amberText : Colors.white)
                    : AppColors.textSecondary,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
              decoration: BoxDecoration(
                color: isSelected
                    ? (isAmber ? AppColors.amberBorder : Colors.white.withOpacity(0.2))
                    : AppColors.surfaceLow,
                borderRadius: BorderRadius.circular(9999),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                  color: isSelected
                      ? (isAmber ? AppColors.amberText : Colors.white)
                      : AppColors.textMuted,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchAndFiltersToolbar() {
    return Row(
      children: [
        // Search Input
        Expanded(
          flex: 6,
          child: TextField(
            onChanged: (v) => setState(() => _searchQuery = v),
            decoration: const InputDecoration(
              prefixIcon: Icon(Icons.search, size: 18, color: AppColors.outline),
              hintText: 'Поиск по ФИО кандидата, желаемой роли или навыкам...',
              contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            ),
          ),
        ),
        const SizedBox(width: 12),

        // Vacancy/Grade Dropdown
        Expanded(
          flex: 3,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.outlineVariant),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedRoleFilter,
                isExpanded: true,
                style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                items: const [
                  DropdownMenuItem(value: 'all', child: Text('Все вакансии и грейды')),
                  DropdownMenuItem(value: 'lead', child: Text('Lead / Principal позиции')),
                  DropdownMenuItem(value: 'senior', child: Text('Senior специалисты')),
                  DropdownMenuItem(value: 'analyst', child: Text('Системные аналитики')),
                  DropdownMenuItem(value: 'ds', child: Text('Data Science & AI')),
                ],
                onChanged: (v) => setState(() => _selectedRoleFilter = v ?? 'all'),
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),

        // Sorting Dropdown
        Expanded(
          flex: 3,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.outlineVariant),
            ),
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _sortOrder,
                isExpanded: true,
                style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                items: const [
                  DropdownMenuItem(value: 'newest', child: Text('По дате (сначала новые)')),
                  DropdownMenuItem(value: 'oldest', child: Text('По дате (сначала старые)')),
                ],
                onChanged: (v) => setState(() => _sortOrder = v ?? 'newest'),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildDataTableCard() {
    final list = _filteredCVs;

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
          // Table Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
            color: AppColors.background,
            child: Row(
              children: const [
                Expanded(flex: 4, child: Text('КАНДИДАТ / ЖЕЛАЕМАЯ ВАКАНСИЯ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textMuted))),
                Expanded(flex: 2, child: Text('ИСХОДНЫЙ ФАЙЛ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textMuted))),
                Expanded(flex: 3, child: Text('ТЕКУЩИЙ СТАТУС ОБРАБОТКИ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textMuted))),
                Expanded(flex: 2, child: Text('ДАТА ДОБАВЛЕНИЯ', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textMuted))),
                SizedBox(width: 160, child: Text('БЫСТРЫЕ ДЕЙСТВИЯ', textAlign: TextAlign.right, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textMuted))),
              ],
            ),
          ),
          const Divider(height: 1, color: AppColors.outlineVariant),

          // Table Rows
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(40),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (list.isEmpty)
            Padding(
              padding: const EdgeInsets.all(60),
              child: Column(
                children: const [
                  Icon(Icons.inbox_outlined, size: 48, color: AppColors.outline),
                  SizedBox(height: 12),
                  Text('Нет резюме по выбранным фильтрам', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppColors.textPrimary)),
                  SizedBox(height: 4),
                  Text('Загрузите файл или сбросьте параметры поиска', style: TextStyle(fontSize: 13, color: AppColors.textMuted)),
                ],
              ),
            )
          else
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: list.length,
              separatorBuilder: (_, __) => const Divider(height: 1, color: AppColors.outlineVariant),
              itemBuilder: (context, index) {
                final cv = list[index];
                final fio = cv.jsonData.fio.isNotEmpty ? cv.jsonData.fio : 'Новый кандидат';
                final vacancy = cv.jsonData.vacancy.isNotEmpty ? cv.jsonData.vacancy : 'Вакансия не указана';
                final totalExp = cv.jsonData.totalYearWork;
                final initials = fio.split(' ').map((s) => s.isNotEmpty ? s[0] : '').take(2).join('');

                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
                  child: Row(
                    children: [
                      // Candidate Info
                      Expanded(
                        flex: 4,
                        child: Row(
                          children: [
                            CircleAvatar(
                              radius: 18,
                              backgroundColor: AppColors.surfaceContainer,
                              child: Text(
                                initials.isNotEmpty ? initials : 'CV',
                                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppColors.secondary),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    fio,
                                    style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppColors.textPrimary),
                                  ),
                                  Text(
                                    totalExp.isNotEmpty ? '$vacancy • $totalExp' : vacancy,
                                    style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),

                      // File Source
                      Expanded(
                        flex: 2,
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppColors.surfaceLow,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: const Text('PDF', style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppColors.secondary)),
                            ),
                            const SizedBox(width: 8),
                            const Text('Резюме.pdf', style: TextStyle(fontSize: 12, color: AppColors.textPrimary)),
                          ],
                        ),
                      ),

                      // Status Badge
                      Expanded(
                        flex: 3,
                        child: _buildStatusBadge(cv.status),
                      ),

                      // Date / Time
                      const Expanded(
                        flex: 2,
                        child: Text('Сегодня', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
                      ),

                      // Actions
                      SizedBox(
                        width: 160,
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
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
                                  ).then((_) => _loadCVs());
                                },
                                icon: const Icon(Icons.rate_review_outlined, size: 14),
                                label: const Text('Валидация'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.amberAccent,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                              )
                            else if (cv.status == 'Готово')
                              ElevatedButton.icon(
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => ResultDownloadScreen(record: cv),
                                    ),
                                  );
                                },
                                icon: const Icon(Icons.download_rounded, size: 14),
                                label: const Text('.docx'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.emeraldText,
                                  foregroundColor: Colors.white,
                                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                  textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                                ),
                              )
                            else
                              OutlinedButton(
                                onPressed: () {
                                  Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => ValidationScreen(
                                        cvId: cv.cvId,
                                        initialData: cv.jsonData,
                                      ),
                                    ),
                                  ).then((_) => _loadCVs());
                                },
                                style: OutlinedButton.styleFrom(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  textStyle: const TextStyle(fontSize: 12),
                                ),
                                child: const Text('Детали'),
                              ),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status) {
    Color bg = AppColors.blueBg;
    Color border = AppColors.blueBorder;
    Color text = AppColors.blueText;
    Color dot = AppColors.secondary;

    if (status == 'Готово') {
      bg = AppColors.emeraldBg;
      border = AppColors.emeraldBorder;
      text = AppColors.emeraldText;
      dot = AppColors.emeraldAccent;
    } else if (status == 'Ожидает проверки HR') {
      bg = AppColors.amberBg;
      border = AppColors.amberBorder;
      text = AppColors.amberText;
      dot = AppColors.amberAccent;
    } else if (status.contains('Ошибк')) {
      bg = AppColors.roseBg;
      border = AppColors.roseBorder;
      text = AppColors.roseText;
      dot = AppColors.error;
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(9999),
            border: Border.all(color: border),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(color: dot, shape: BoxShape.circle),
              ),
              const SizedBox(width: 6),
              Text(
                status,
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: text),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
