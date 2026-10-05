import 'package:flutter/material.dart';

class AppTheme {
  static const ink = Color(0xFF202724);
  static const muted = Color(0xFF58635D);
  static const rule = Color(0xFFDBE2DD);
  static const green = Color(0xFF146346);
  static const greenHover = Color(0xFF0C4D35);
  static const soft = Color(0xFFF2F6F3);
  static const danger = Color(0xFFA13D35);
  static const warning = Color(0xFF805314);

  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: green).copyWith(
      primary: green,
      onPrimary: Colors.white,
      primaryContainer: soft,
      onPrimaryContainer: ink,
      secondary: muted,
      onSecondary: Colors.white,
      surface: Colors.white,
      onSurface: ink,
      outline: rule,
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
          borderSide: const BorderSide(color: rule),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: green, width: 2),
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      dividerColor: rule,
      focusColor: green,
      hoverColor: greenHover.withValues(alpha: 0.08),
      splashColor: green.withValues(alpha: 0.08),
    );
  }
}
