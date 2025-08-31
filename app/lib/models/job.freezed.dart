// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'job.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$Job {

// This field will be added by the backend function.
 String? get userId;@JsonKey(unknownEnumValue: JobStatus.unknown) JobStatus get status; String? get transcribedText; String? get childExplanation; String? get parentHint; String? get illustrationPrompt; String? get imageGcsPath; String? get finalAudioGcsPath; String? get errorMessage;
/// Create a copy of Job
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$JobCopyWith<Job> get copyWith => _$JobCopyWithImpl<Job>(this as Job, _$identity);

  /// Serializes this Job to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is Job&&(identical(other.userId, userId) || other.userId == userId)&&(identical(other.status, status) || other.status == status)&&(identical(other.transcribedText, transcribedText) || other.transcribedText == transcribedText)&&(identical(other.childExplanation, childExplanation) || other.childExplanation == childExplanation)&&(identical(other.parentHint, parentHint) || other.parentHint == parentHint)&&(identical(other.illustrationPrompt, illustrationPrompt) || other.illustrationPrompt == illustrationPrompt)&&(identical(other.imageGcsPath, imageGcsPath) || other.imageGcsPath == imageGcsPath)&&(identical(other.finalAudioGcsPath, finalAudioGcsPath) || other.finalAudioGcsPath == finalAudioGcsPath)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,userId,status,transcribedText,childExplanation,parentHint,illustrationPrompt,imageGcsPath,finalAudioGcsPath,errorMessage);

@override
String toString() {
  return 'Job(userId: $userId, status: $status, transcribedText: $transcribedText, childExplanation: $childExplanation, parentHint: $parentHint, illustrationPrompt: $illustrationPrompt, imageGcsPath: $imageGcsPath, finalAudioGcsPath: $finalAudioGcsPath, errorMessage: $errorMessage)';
}


}

/// @nodoc
abstract mixin class $JobCopyWith<$Res>  {
  factory $JobCopyWith(Job value, $Res Function(Job) _then) = _$JobCopyWithImpl;
@useResult
$Res call({
 String? userId,@JsonKey(unknownEnumValue: JobStatus.unknown) JobStatus status, String? transcribedText, String? childExplanation, String? parentHint, String? illustrationPrompt, String? imageGcsPath, String? finalAudioGcsPath, String? errorMessage
});




}
/// @nodoc
class _$JobCopyWithImpl<$Res>
    implements $JobCopyWith<$Res> {
  _$JobCopyWithImpl(this._self, this._then);

  final Job _self;
  final $Res Function(Job) _then;

/// Create a copy of Job
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? userId = freezed,Object? status = null,Object? transcribedText = freezed,Object? childExplanation = freezed,Object? parentHint = freezed,Object? illustrationPrompt = freezed,Object? imageGcsPath = freezed,Object? finalAudioGcsPath = freezed,Object? errorMessage = freezed,}) {
  return _then(_self.copyWith(
userId: freezed == userId ? _self.userId : userId // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as JobStatus,transcribedText: freezed == transcribedText ? _self.transcribedText : transcribedText // ignore: cast_nullable_to_non_nullable
as String?,childExplanation: freezed == childExplanation ? _self.childExplanation : childExplanation // ignore: cast_nullable_to_non_nullable
as String?,parentHint: freezed == parentHint ? _self.parentHint : parentHint // ignore: cast_nullable_to_non_nullable
as String?,illustrationPrompt: freezed == illustrationPrompt ? _self.illustrationPrompt : illustrationPrompt // ignore: cast_nullable_to_non_nullable
as String?,imageGcsPath: freezed == imageGcsPath ? _self.imageGcsPath : imageGcsPath // ignore: cast_nullable_to_non_nullable
as String?,finalAudioGcsPath: freezed == finalAudioGcsPath ? _self.finalAudioGcsPath : finalAudioGcsPath // ignore: cast_nullable_to_non_nullable
as String?,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}

}


/// Adds pattern-matching-related methods to [Job].
extension JobPatterns on Job {
/// A variant of `map` that fallback to returning `orElse`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _Job value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _Job() when $default != null:
return $default(_that);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// Callbacks receives the raw object, upcasted.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case final Subclass2 value:
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _Job value)  $default,){
final _that = this;
switch (_that) {
case _Job():
return $default(_that);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `map` that fallback to returning `null`.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case final Subclass value:
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _Job value)?  $default,){
final _that = this;
switch (_that) {
case _Job() when $default != null:
return $default(_that);case _:
  return null;

}
}
/// A variant of `when` that fallback to an `orElse` callback.
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return orElse();
/// }
/// ```

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String? userId, @JsonKey(unknownEnumValue: JobStatus.unknown)  JobStatus status,  String? transcribedText,  String? childExplanation,  String? parentHint,  String? illustrationPrompt,  String? imageGcsPath,  String? finalAudioGcsPath,  String? errorMessage)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _Job() when $default != null:
return $default(_that.userId,_that.status,_that.transcribedText,_that.childExplanation,_that.parentHint,_that.illustrationPrompt,_that.imageGcsPath,_that.finalAudioGcsPath,_that.errorMessage);case _:
  return orElse();

}
}
/// A `switch`-like method, using callbacks.
///
/// As opposed to `map`, this offers destructuring.
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case Subclass2(:final field2):
///     return ...;
/// }
/// ```

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String? userId, @JsonKey(unknownEnumValue: JobStatus.unknown)  JobStatus status,  String? transcribedText,  String? childExplanation,  String? parentHint,  String? illustrationPrompt,  String? imageGcsPath,  String? finalAudioGcsPath,  String? errorMessage)  $default,) {final _that = this;
switch (_that) {
case _Job():
return $default(_that.userId,_that.status,_that.transcribedText,_that.childExplanation,_that.parentHint,_that.illustrationPrompt,_that.imageGcsPath,_that.finalAudioGcsPath,_that.errorMessage);case _:
  throw StateError('Unexpected subclass');

}
}
/// A variant of `when` that fallback to returning `null`
///
/// It is equivalent to doing:
/// ```dart
/// switch (sealedClass) {
///   case Subclass(:final field):
///     return ...;
///   case _:
///     return null;
/// }
/// ```

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String? userId, @JsonKey(unknownEnumValue: JobStatus.unknown)  JobStatus status,  String? transcribedText,  String? childExplanation,  String? parentHint,  String? illustrationPrompt,  String? imageGcsPath,  String? finalAudioGcsPath,  String? errorMessage)?  $default,) {final _that = this;
switch (_that) {
case _Job() when $default != null:
return $default(_that.userId,_that.status,_that.transcribedText,_that.childExplanation,_that.parentHint,_that.illustrationPrompt,_that.imageGcsPath,_that.finalAudioGcsPath,_that.errorMessage);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _Job implements Job {
  const _Job({this.userId, @JsonKey(unknownEnumValue: JobStatus.unknown) required this.status, this.transcribedText, this.childExplanation, this.parentHint, this.illustrationPrompt, this.imageGcsPath, this.finalAudioGcsPath, this.errorMessage});
  factory _Job.fromJson(Map<String, dynamic> json) => _$JobFromJson(json);

// This field will be added by the backend function.
@override final  String? userId;
@override@JsonKey(unknownEnumValue: JobStatus.unknown) final  JobStatus status;
@override final  String? transcribedText;
@override final  String? childExplanation;
@override final  String? parentHint;
@override final  String? illustrationPrompt;
@override final  String? imageGcsPath;
@override final  String? finalAudioGcsPath;
@override final  String? errorMessage;

/// Create a copy of Job
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$JobCopyWith<_Job> get copyWith => __$JobCopyWithImpl<_Job>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$JobToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _Job&&(identical(other.userId, userId) || other.userId == userId)&&(identical(other.status, status) || other.status == status)&&(identical(other.transcribedText, transcribedText) || other.transcribedText == transcribedText)&&(identical(other.childExplanation, childExplanation) || other.childExplanation == childExplanation)&&(identical(other.parentHint, parentHint) || other.parentHint == parentHint)&&(identical(other.illustrationPrompt, illustrationPrompt) || other.illustrationPrompt == illustrationPrompt)&&(identical(other.imageGcsPath, imageGcsPath) || other.imageGcsPath == imageGcsPath)&&(identical(other.finalAudioGcsPath, finalAudioGcsPath) || other.finalAudioGcsPath == finalAudioGcsPath)&&(identical(other.errorMessage, errorMessage) || other.errorMessage == errorMessage));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,userId,status,transcribedText,childExplanation,parentHint,illustrationPrompt,imageGcsPath,finalAudioGcsPath,errorMessage);

@override
String toString() {
  return 'Job(userId: $userId, status: $status, transcribedText: $transcribedText, childExplanation: $childExplanation, parentHint: $parentHint, illustrationPrompt: $illustrationPrompt, imageGcsPath: $imageGcsPath, finalAudioGcsPath: $finalAudioGcsPath, errorMessage: $errorMessage)';
}


}

/// @nodoc
abstract mixin class _$JobCopyWith<$Res> implements $JobCopyWith<$Res> {
  factory _$JobCopyWith(_Job value, $Res Function(_Job) _then) = __$JobCopyWithImpl;
@override @useResult
$Res call({
 String? userId,@JsonKey(unknownEnumValue: JobStatus.unknown) JobStatus status, String? transcribedText, String? childExplanation, String? parentHint, String? illustrationPrompt, String? imageGcsPath, String? finalAudioGcsPath, String? errorMessage
});




}
/// @nodoc
class __$JobCopyWithImpl<$Res>
    implements _$JobCopyWith<$Res> {
  __$JobCopyWithImpl(this._self, this._then);

  final _Job _self;
  final $Res Function(_Job) _then;

/// Create a copy of Job
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? userId = freezed,Object? status = null,Object? transcribedText = freezed,Object? childExplanation = freezed,Object? parentHint = freezed,Object? illustrationPrompt = freezed,Object? imageGcsPath = freezed,Object? finalAudioGcsPath = freezed,Object? errorMessage = freezed,}) {
  return _then(_Job(
userId: freezed == userId ? _self.userId : userId // ignore: cast_nullable_to_non_nullable
as String?,status: null == status ? _self.status : status // ignore: cast_nullable_to_non_nullable
as JobStatus,transcribedText: freezed == transcribedText ? _self.transcribedText : transcribedText // ignore: cast_nullable_to_non_nullable
as String?,childExplanation: freezed == childExplanation ? _self.childExplanation : childExplanation // ignore: cast_nullable_to_non_nullable
as String?,parentHint: freezed == parentHint ? _self.parentHint : parentHint // ignore: cast_nullable_to_non_nullable
as String?,illustrationPrompt: freezed == illustrationPrompt ? _self.illustrationPrompt : illustrationPrompt // ignore: cast_nullable_to_non_nullable
as String?,imageGcsPath: freezed == imageGcsPath ? _self.imageGcsPath : imageGcsPath // ignore: cast_nullable_to_non_nullable
as String?,finalAudioGcsPath: freezed == finalAudioGcsPath ? _self.finalAudioGcsPath : finalAudioGcsPath // ignore: cast_nullable_to_non_nullable
as String?,errorMessage: freezed == errorMessage ? _self.errorMessage : errorMessage // ignore: cast_nullable_to_non_nullable
as String?,
  ));
}


}

// dart format on
