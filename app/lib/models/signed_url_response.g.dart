// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'signed_url_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SignedUrlResponse _$SignedUrlResponseFromJson(Map<String, dynamic> json) =>
    _SignedUrlResponse(
      jobId: json['jobId'] as String,
      signedUrl: json['signedUrl'] as String,
      expiresIn: (json['expiresIn'] as num).toInt(),
      requiredHeaders: Map<String, String>.from(json['requiredHeaders'] as Map),
    );

Map<String, dynamic> _$SignedUrlResponseToJson(_SignedUrlResponse instance) =>
    <String, dynamic>{
      'jobId': instance.jobId,
      'signedUrl': instance.signedUrl,
      'expiresIn': instance.expiresIn,
      'requiredHeaders': instance.requiredHeaders,
    };
