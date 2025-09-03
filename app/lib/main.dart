import 'package:app/screens/home_screen.dart';
import 'package:app/firebase_options.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

Future<void> main() async {
  // Ensure that Flutter bindings are initialized before any Flutter-specific code.
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Firebase with the retrieved options.
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  // In debug mode, connect to the local Firebase Emulator Suite.
  if (kDebugMode) {
    try {
      const host = 'localhost';
      FirebaseFirestore.instance.useFirestoreEmulator(host, 8080);
      FirebaseStorage.instance.useStorageEmulator(host, 9199);
      FirebaseFunctions.instanceFor(
        region: 'asia-northeast1',
      ).useFunctionsEmulator(host, 5001);
    } catch (e) {
      // ignore: avoid_print
      print(e);
    }
  }

  // Wrap the app with ProviderScope to make Riverpod available throughout the app.
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
        textTheme: GoogleFonts.mPlusRounded1cTextTheme(
          Theme.of(context).textTheme,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
