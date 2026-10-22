import 'package:flutter/material.dart';

class AppColors {
  // Brand & Foundation (HR Enterprise Suite)
  static const Color background = Color(0xFFF8F9FF);           // Calm slate-tinted canvas
  static const Color surface = Color(0xFFFFFFFF);              // Clean white card surface
  static const Color surfaceLow = Color(0xFFEFF4FF);           // Subtle container low
  static const Color surfaceContainer = Color(0xFFE5EEFF);     // Tonal container
  static const Color surfaceHigh = Color(0xFFDCE9FF);          // Elevated container
  static const Color surfaceHighest = Color(0xFFD3E4FE);       // High-contrast container

  static const Color primary = Color(0xFF091426);              // Deep slate navy for headers and titles
  static const Color primaryContainer = Color(0xFF1E293B);
  static const Color onPrimary = Color(0xFFFFFFFF);
  static const Color onPrimaryContainer = Color(0xFF8590A6);

  static const Color secondary = Color(0xFF0051D5);            // Brand Accent Royal Blue
  static const Color secondaryContainer = Color(0xFF316BF3);
  static const Color onSecondary = Color(0xFFFFFFFF);

  // Typography Colors
  static const Color textPrimary = Color(0xFF0B1C30);          // High-contrast navy text
  static const Color textSecondary = Color(0xFF45474C);        // Medium slate text
  static const Color textMuted = Color(0xFF64748B);            // Secondary / muted slate
  static const Color outline = Color(0xFF75777D);              // Outline borders / icons
  static const Color outlineVariant = Color(0xFFE2E8F0);       // Whisper-quiet single-pixel border

  // Semantic Status Badges
  // 1. Pending HR Validation (Attention Amber)
  static const Color amberBg = Color(0xFFFFFBEB);
  static const Color amberBorder = Color(0xFFFDE68A);
  static const Color amberText = Color(0xFFD97706);
  static const Color amberAccent = Color(0xFFF59E0B);

  // 2. Ready / Screened (Emerald Green)
  static const Color emeraldBg = Color(0xFFECFDF5);
  static const Color emeraldBorder = Color(0xFFA7F3D0);
  static const Color emeraldText = Color(0xFF059669);
  static const Color emeraldAccent = Color(0xFF10B981);

  // 3. Intake / Uploaded / In Progress (Royal Blue)
  static const Color blueBg = Color(0xFFEFF6FF);
  static const Color blueBorder = Color(0xFFBFDBFE);
  static const Color blueText = Color(0xFF2563EB);

  // 4. Error / Rejection (Crimson Rose)
  static const Color roseBg = Color(0xFFFFF1F2);
  static const Color roseBorder = Color(0xFFFECDD3);
  static const Color roseText = Color(0xFFE11D48);
  static const Color error = Color(0xFFBA1A1A);
  static const Color errorContainer = Color(0xFFFFDAD6);
  static const Color onErrorContainer = Color(0xFF93000A);

  // 5. LLM / Gemma-3 (Violet Purple)
  static const Color purpleBg = Color(0xFFFAF5FF);
  static const Color purpleBorder = Color(0xFFE9D5FF);
  static const Color purpleText = Color(0xFF7E22CE);
}

class AppTheme {
  static ThemeData get enterpriseTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: AppColors.background,
      fontFamily: 'Inter',
      colorScheme: const ColorScheme.light(
        primary: AppColors.primary,
        onPrimary: AppColors.onPrimary,
        secondary: AppColors.secondary,
        onSecondary: AppColors.onSecondary,
        surface: AppColors.surface,
        onSurface: AppColors.textPrimary,
        error: AppColors.error,
        background: AppColors.background,
      ),
      cardTheme: CardTheme(
        color: AppColors.surface,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.outlineVariant, width: 1),
        ),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: AppColors.textPrimary,
        elevation: 0,
        scrolledUnderElevation: 1,
        centerTitle: false,
        titleTextStyle: TextStyle(
          color: AppColors.primary,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          fontFamily: 'Plus Jakarta Sans',
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.outlineVariant, width: 1),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.outlineVariant, width: 1),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.secondary, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.error, width: 1),
        ),
        labelStyle: const TextStyle(color: AppColors.textSecondary, fontSize: 13),
        hintStyle: const TextStyle(color: AppColors.outline, fontSize: 13),
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.secondary,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            fontFamily: 'Inter',
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.textPrimary,
          backgroundColor: Colors.white,
          side: const BorderSide(color: AppColors.outlineVariant, width: 1),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
          ),
          textStyle: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            fontFamily: 'Inter',
          ),
        ),
      ),
    );
  }

  // Fallback for darkTheme reference
  static ThemeData get darkTheme => enterpriseTheme;
}
