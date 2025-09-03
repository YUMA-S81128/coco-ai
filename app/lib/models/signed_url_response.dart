import 'package:freezed_annotation/freezed_annotation.dart';

part 'signed_url_response.freezed.dart';
part 'signed_url_response.g.dart';

@freezed
abstract class SignedUrlResponse with _$SignedUrlResponse {
  const factory SignedUrlResponse({
    required String jobId,
    required String signedUrl,
    required int expiresIn,
    required Map<String, String> requiredHeaders,
  }) = _SignedUrlResponse;

  factory SignedUrlResponse.fromJson(Map<String, dynamic> json) =>
      _$SignedUrlResponseFromJson(json);
}
