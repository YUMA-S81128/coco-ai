import 'package:app/screens/home_screen.dart';
import 'package:app/firebase_options.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_app_check/firebase_app_check.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart' show kDebugMode;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

Future<void> main() async {
  // Flutterのコードを実行する前に、Flutterバインディングが初期化されていることを確認
  WidgetsFlutterBinding.ensureInitialized();

  // Firebaseを初期化
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // App Checkを有効化。
  // Webでは、開発・本番ともにreCAPTCHA v3を使用
  const recaptchaSiteKey = String.fromEnvironment('RECAPTCHA_V3_SITE_KEY');
  if (recaptchaSiteKey.isEmpty) {
    debugPrint(
      '警告: RECAPTCHA_V3_SITE_KEYが設定されていません。ローカル実行時は --dart-define を使用してください。',
    );
  }

  await FirebaseAppCheck.instance.activate(
    webProvider: ReCaptchaV3Provider(recaptchaSiteKey),
    // モバイルは開発時と本番時でプロバイダを切り替える
    // 現在はWebのみのため、コメントアウト
    // androidProvider: kDebugMode
    //     ? AndroidProvider.debug
    //     : AndroidProvider.playIntegrity,
    // appleProvider: kDebugMode ? AppleProvider.debug : AppleProvider.appAttest,
  );
  debugPrint('App Checkが有効化されました (Mode: ${kDebugMode ? "Debug" : "Release"})');

  // 匿名認証でサインインし、ユニークなユーザーIDを取得
  try {
    await FirebaseAuth.instance.signInAnonymously();
    debugPrint('匿名認証でサインインしました: ${FirebaseAuth.instance.currentUser?.uid}');
  } catch (e) {
    debugPrint('匿名認証でのサインインに失敗しました: $e');
  }

  // RiverpodのDIコンテナを準備
  final container = ProviderContainer();

  runApp(UncontrolledProviderScope(container: container, child: const MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Coco-Ai',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.lightBlue),
        textTheme: GoogleFonts.mPlusRounded1cTextTheme(
          Theme.of(context).textTheme,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
