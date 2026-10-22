class EducationItem {
  String type;
  String institution;
  String speciality;
  String year;

  EducationItem({
    this.type = 'Высшее:',
    this.institution = '',
    this.speciality = '',
    this.year = '',
  });

  factory EducationItem.fromJson(Map<String, dynamic> json) {
    return EducationItem(
      type: json['type'] ?? 'Высшее:',
      institution: json['institution'] ?? '',
      speciality: json['speciality'] ?? '',
      year: json['year'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'type': type,
      'institution': institution,
      'speciality': speciality,
      'year': year,
    };
  }
}

class AdvancedTrainingItem {
  String name;
  String year;

  AdvancedTrainingItem({
    this.name = '',
    this.year = '',
  });

  factory AdvancedTrainingItem.fromJson(Map<String, dynamic> json) {
    return AdvancedTrainingItem(
      name: json['name'] ?? '',
      year: json['year'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'year': year,
    };
  }
}

class ProjectItem {
  String placeTimeRaw;
  String period;
  String roleInProject;
  List<String> taskOnProject;
  List<String> achievementsInProject;
  String skillsToolsInProject;

  ProjectItem({
    this.placeTimeRaw = '',
    this.period = '',
    this.roleInProject = '',
    List<String>? taskOnProject,
    List<String>? achievementsInProject,
    this.skillsToolsInProject = '',
  })  : taskOnProject = taskOnProject ?? [],
        achievementsInProject = achievementsInProject ?? [];

  factory ProjectItem.fromJson(Map<String, dynamic> json) {
    return ProjectItem(
      placeTimeRaw: json['place_time_raw'] ?? '',
      period: json['period'] ?? '',
      roleInProject: json['role_in_project'] ?? '',
      taskOnProject: (json['task_on_project'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      achievementsInProject: (json['achievements_in_project'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      skillsToolsInProject: json['skills_tools_in_project'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'place_time_raw': placeTimeRaw,
      'period': period,
      'role_in_project': roleInProject,
      'task_on_project': taskOnProject,
      'achievements_in_project': achievementsInProject,
      'skills_tools_in_project': skillsToolsInProject,
    };
  }
}

class CVJsonData {
  String fio;
  String vacancy;
  String totalYearWork;
  String projectBackround;
  String pitch;
  List<String> skillsAndTools;
  List<EducationItem> education;
  List<AdvancedTrainingItem> advancedTraining;
  String languages;
  String citizenshipLocation;
  String employment;
  String status;
  List<ProjectItem> projects;
  String? reworkComment;

  CVJsonData({
    this.fio = '',
    this.vacancy = '',
    this.totalYearWork = '',
    this.projectBackround = '',
    this.pitch = '',
    List<String>? skillsAndTools,
    List<EducationItem>? education,
    List<AdvancedTrainingItem>? advancedTraining,
    this.languages = 'Английский на уровне A2',
    this.citizenshipLocation = '',
    this.employment = 'Полная занятость, удаленная работа',
    this.status = 'Готов к переезду',
    List<ProjectItem>? projects,
    this.reworkComment,
  })  : skillsAndTools = skillsAndTools ?? [],
        education = education ?? [],
        advancedTraining = advancedTraining ?? [],
        projects = projects ?? [];

  factory CVJsonData.fromJson(Map<String, dynamic> json) {
    return CVJsonData(
      fio: json['fio'] ?? '',
      vacancy: json['vacancy'] ?? '',
      totalYearWork: json['total_year_work'] ?? '',
      projectBackround: json['project_backround'] ?? '',
      pitch: json['pitch'] ?? '',
      skillsAndTools: (json['skills_and_tools'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          [],
      education: (json['education'] as List<dynamic>?)
              ?.map((e) => EducationItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      advancedTraining: (json['advanced_training'] as List<dynamic>?)
              ?.map((e) => AdvancedTrainingItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      languages: json['languages'] ?? 'Английский на уровне A2',
      citizenshipLocation: json['citizenship_location'] ?? '',
      employment: json['employment'] ?? 'Полная занятость, удаленная работа',
      status: json['status'] ?? 'Готов к переезду',
      projects: (json['projects'] as List<dynamic>?)
              ?.map((e) => ProjectItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      reworkComment: json['_rework_comment'] ?? json['rework_comment'],
    );
  }

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'fio': fio,
      'vacancy': vacancy,
      'total_year_work': totalYearWork,
      'project_backround': projectBackround,
      'pitch': pitch,
      'skills_and_tools': skillsAndTools,
      'education': education.map((e) => e.toJson()).toList(),
      'advanced_training': advancedTraining.map((e) => e.toJson()).toList(),
      'languages': languages,
      'citizenship_location': citizenshipLocation,
      'employment': employment,
      'status': status,
      'projects': projects.map((e) => e.toJson()).toList(),
    };
    if (reworkComment != null) {
      map['_rework_comment'] = reworkComment;
    }
    return map;
  }
}

class CVRecord {
  final int cvId;
  final int hrId;
  final String status;
  final CVJsonData jsonData;
  final String? docx;
  final String? downloadUrl;

  CVRecord({
    required this.cvId,
    required this.hrId,
    required this.status,
    required this.jsonData,
    this.docx,
    this.downloadUrl,
  });

  factory CVRecord.fromJson(Map<String, dynamic> json) {
    final rawJsonb = json['jsonb'] ?? json['data'] ?? {};
    return CVRecord(
      cvId: json['cv_id'] ?? 0,
      hrId: json['hr_id'] ?? 0,
      status: json['status'] ?? 'Загружено',
      jsonData: CVJsonData.fromJson(rawJsonb),
      docx: json['docx'],
      downloadUrl: json['download_url'],
    );
  }
}
