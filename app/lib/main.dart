import 'package:app/providers/firebase_providers.dart';
import 'package:app/constants/firebase_constants.dart';
import 'package:app/screens/home_screen.dart';
import 'package:app/firebase_options.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

Future<void> main() async {
  // Flutterのコードを実行する前に、Flutterバインディングが初期化されていることを確認
  WidgetsFlutterBinding.ensureInitialized();

  // Firebaseを初期化
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // 匿名認証でサインインし、ユニークなユーザーIDを取得
  try {
    await FirebaseAuth.instance.signInAnonymously();
    debugPrint('匿名認証でサインインしました: ${FirebaseAuth.instance.currentUser?.uid}');
  } catch (e) {
    debugPrint('匿名認証でのサインインに失敗しました: $e');
  }

  // RiverpodのDIコンテナを準備
  final container = ProviderContainer();

  // Firebase Emulator Suiteへの接続、または本番環境のFunctions接続設定
  try {
    if (kDebugMode) {
      // デバッグモードの場合、ローカルのFirebase Emulator Suiteに接続
      const host = 'localhost';
      container.read(firestoreProvider).useFirestoreEmulator(host, 8080);
      container.read(firebaseStorageProvider).useStorageEmulator(host, 9199);
      container.read(functionsProvider).useFunctionsEmulator(host, 5001);
      debugPrint('ローカルエミュレータに接続しました。');
    } else {
      // 本番環境では、Firebase Hostingのrewrites経由でFunctionsを呼び出す
      final functions = container.read(functionsProvider);
      functions.useFunctionsEmulator(FirebaseConstants.functionsOrigin, 443);
      debugPrint('本番環境のFunctionsオリジンを設定しました。');
    }
  } catch (e) {
    // どちらかの設定で失敗した場合にエラーを記録
    debugPrint('Firebaseサービスの接続設定に失敗しました: $e');
  }

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
