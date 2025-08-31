import 'package:flutter_riverpod/flutter_riverpod.dart';

/// A provider for the [AuthService].
final authServiceProvider = Provider((ref) => AuthService());

/// A service class for handling authentication.
///
/// In the future, this will be replaced with a real Firebase Authentication implementation.
class AuthService {
  /// Returns the current user's ID.
  /// Returns a mock ID for now.
  String? get currentUserId => 'mock-user-id-12345';
}
