import 'package:flutter/material.dart';

class AppTheme {
  static const ink = Color(0xFF202020);
  static const muted = Color(0xFF666666);
  static const rule = Color(0xFFE5E5E5);
  static const primary = Color(0xFF262626);
  static const primaryHover = Color(0xFF111111);
  static const soft = Color(0xFFF5F5F5);
  static const success = Color(0xFF276749);
  static const danger = Color(0xFFA13D35);
  static const warning = Color(0xFF805314);

  static ThemeData light() {
    final scheme = const ColorScheme.light(
      primary: primary,
      onPrimary: Colors.white,
      primaryContainer: soft,
      onPrimaryContainer: ink,
      secondary: muted,
      onSecondary: Colors.white,
      surface: Colors.white,
      onSurface: ink,
      outline: muted,
      outlineVariant: rule,
      secondaryContainer: soft,
      onSecondaryContainer: ink,
      tertiary: muted,
      onTertiary: Colors.white,
      tertiaryContainer: soft,
      onTertiaryContainer: ink,
      surfaceContainerLowest: Colors.white,
      surfaceContainerLow: soft,
      surfaceContainer: soft,
      surfaceContainerHigh: rule,
      surfaceContainerHighest: rule,
      inverseSurface: ink,
      onInverseSurface: Colors.white,
      inversePrimary: Colors.white,
      surfaceTint: Colors.transparent,
      error: danger,
      onError: Colors.white,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: Colors.white,
      appBarTheme: const AppBarTheme(
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: ink,
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      ),
      navigationBarTheme: const NavigationBarThemeData(
        backgroundColor: Colors.white,
        indicatorColor: rule,
      ),
      cardTheme: CardThemeData(
        color: soft,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: soft,
        enabledBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: muted),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: primary, width: 2),
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dividerColor: rule,
      focusColor: primary,
      hoverColor: primaryHover.withValues(alpha: 0.08),
      splashColor: primary.withValues(alpha: 0.08),
    );
  }
}
