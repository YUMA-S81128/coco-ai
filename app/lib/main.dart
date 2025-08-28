import 'package:app/screens/home_screen.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

Future<void> main() async {
  // Flutterアプリの初期化を保証
  WidgetsFlutterBinding.ensureInitialized();

  // --dart-define-from-file で渡された環境変数からFirebaseの接続情報を取得
  const apiKey = String.fromEnvironment('FIREBASE_API_KEY');
  const appId = String.fromEnvironment('FIREBASE_APP_ID');
  const messagingSenderId = String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID');
  const projectId = String.fromEnvironment('FIREBASE_PROJECT_ID');
  const storageBucket = String.fromEnvironment('FIREBASE_STORAGE_BUCKET');
  const authDomain = String.fromEnvironment('FIREBASE_AUTH_DOMAIN');

  // Firebaseの初期化
  await Firebase.initializeApp(
    options: const FirebaseOptions(
      apiKey: apiKey,
      appId: appId,
      messagingSenderId: messagingSenderId,
      projectId: projectId,
      storageBucket: storageBucket,
      authDomain: authDomain,
    ),
  );

  // Riverpodをアプリ全体で使えるようにProviderScopeでラップ
  runApp(const ProviderScope(child: MyApp()));
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
        // アプリ全体のフォントを、丸みがあって親しみやすいフォントに設定
        textTheme: GoogleFonts.mPlusRounded1cTextTheme(
          Theme.of(context).textTheme,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
