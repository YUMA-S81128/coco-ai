import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// A provider for the [AuthService].
final authServiceProvider = Provider(
  (ref) => AuthService(FirebaseAuth.instance),
);

/// A service class for handling authentication.
class AuthService {
  final FirebaseAuth _auth;

  AuthService(this._auth);

  /// Returns the current user's ID.
  /// Returns null if the user is not signed in.
  String? get currentUserId => _auth.currentUser?.uid;
}
