import 'package:app/constants/firebase_constants.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:cloud_functions/cloud_functions.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// FirebaseFirestore のインスタンスを提供するプロバイダー
final firestoreProvider = Provider((ref) => FirebaseFirestore.instance);

/// FirebaseStorage のインスタンスを提供するプロバイダー
final firebaseStorageProvider = Provider((ref) => FirebaseStorage.instance);

/// FirebaseFunctions のインスタンスを提供するプロバイダー
final functionsProvider = Provider(
  (ref) => FirebaseFunctions.instanceFor(region: FirebaseConstants.region),
);
