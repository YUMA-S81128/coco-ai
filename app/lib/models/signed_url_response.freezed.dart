// GENERATED CODE - DO NOT MODIFY BY HAND
// coverage:ignore-file
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'signed_url_response.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

// dart format off
T _$identity<T>(T value) => value;

/// @nodoc
mixin _$SignedUrlResponse {

 String get jobId; String get signedUrl; int get expiresIn; Map<String, String> get requiredHeaders;
/// Create a copy of SignedUrlResponse
/// with the given fields replaced by the non-null parameter values.
@JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
$SignedUrlResponseCopyWith<SignedUrlResponse> get copyWith => _$SignedUrlResponseCopyWithImpl<SignedUrlResponse>(this as SignedUrlResponse, _$identity);

  /// Serializes this SignedUrlResponse to a JSON map.
  Map<String, dynamic> toJson();


@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is SignedUrlResponse&&(identical(other.jobId, jobId) || other.jobId == jobId)&&(identical(other.signedUrl, signedUrl) || other.signedUrl == signedUrl)&&(identical(other.expiresIn, expiresIn) || other.expiresIn == expiresIn)&&const DeepCollectionEquality().equals(other.requiredHeaders, requiredHeaders));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,jobId,signedUrl,expiresIn,const DeepCollectionEquality().hash(requiredHeaders));

@override
String toString() {
  return 'SignedUrlResponse(jobId: $jobId, signedUrl: $signedUrl, expiresIn: $expiresIn, requiredHeaders: $requiredHeaders)';
}


}

/// @nodoc
abstract mixin class $SignedUrlResponseCopyWith<$Res>  {
  factory $SignedUrlResponseCopyWith(SignedUrlResponse value, $Res Function(SignedUrlResponse) _then) = _$SignedUrlResponseCopyWithImpl;
@useResult
$Res call({
 String jobId, String signedUrl, int expiresIn, Map<String, String> requiredHeaders
});




}
/// @nodoc
class _$SignedUrlResponseCopyWithImpl<$Res>
    implements $SignedUrlResponseCopyWith<$Res> {
  _$SignedUrlResponseCopyWithImpl(this._self, this._then);

  final SignedUrlResponse _self;
  final $Res Function(SignedUrlResponse) _then;

/// Create a copy of SignedUrlResponse
/// with the given fields replaced by the non-null parameter values.
@pragma('vm:prefer-inline') @override $Res call({Object? jobId = null,Object? signedUrl = null,Object? expiresIn = null,Object? requiredHeaders = null,}) {
  return _then(_self.copyWith(
jobId: null == jobId ? _self.jobId : jobId // ignore: cast_nullable_to_non_nullable
as String,signedUrl: null == signedUrl ? _self.signedUrl : signedUrl // ignore: cast_nullable_to_non_nullable
as String,expiresIn: null == expiresIn ? _self.expiresIn : expiresIn // ignore: cast_nullable_to_non_nullable
as int,requiredHeaders: null == requiredHeaders ? _self.requiredHeaders : requiredHeaders // ignore: cast_nullable_to_non_nullable
as Map<String, String>,
  ));
}

}


/// Adds pattern-matching-related methods to [SignedUrlResponse].
extension SignedUrlResponsePatterns on SignedUrlResponse {
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

@optionalTypeArgs TResult maybeMap<TResult extends Object?>(TResult Function( _SignedUrlResponse value)?  $default,{required TResult orElse(),}){
final _that = this;
switch (_that) {
case _SignedUrlResponse() when $default != null:
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

@optionalTypeArgs TResult map<TResult extends Object?>(TResult Function( _SignedUrlResponse value)  $default,){
final _that = this;
switch (_that) {
case _SignedUrlResponse():
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

@optionalTypeArgs TResult? mapOrNull<TResult extends Object?>(TResult? Function( _SignedUrlResponse value)?  $default,){
final _that = this;
switch (_that) {
case _SignedUrlResponse() when $default != null:
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

@optionalTypeArgs TResult maybeWhen<TResult extends Object?>(TResult Function( String jobId,  String signedUrl,  int expiresIn,  Map<String, String> requiredHeaders)?  $default,{required TResult orElse(),}) {final _that = this;
switch (_that) {
case _SignedUrlResponse() when $default != null:
return $default(_that.jobId,_that.signedUrl,_that.expiresIn,_that.requiredHeaders);case _:
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

@optionalTypeArgs TResult when<TResult extends Object?>(TResult Function( String jobId,  String signedUrl,  int expiresIn,  Map<String, String> requiredHeaders)  $default,) {final _that = this;
switch (_that) {
case _SignedUrlResponse():
return $default(_that.jobId,_that.signedUrl,_that.expiresIn,_that.requiredHeaders);case _:
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

@optionalTypeArgs TResult? whenOrNull<TResult extends Object?>(TResult? Function( String jobId,  String signedUrl,  int expiresIn,  Map<String, String> requiredHeaders)?  $default,) {final _that = this;
switch (_that) {
case _SignedUrlResponse() when $default != null:
return $default(_that.jobId,_that.signedUrl,_that.expiresIn,_that.requiredHeaders);case _:
  return null;

}
}

}

/// @nodoc
@JsonSerializable()

class _SignedUrlResponse implements SignedUrlResponse {
  const _SignedUrlResponse({required this.jobId, required this.signedUrl, required this.expiresIn, required final  Map<String, String> requiredHeaders}): _requiredHeaders = requiredHeaders;
  factory _SignedUrlResponse.fromJson(Map<String, dynamic> json) => _$SignedUrlResponseFromJson(json);

@override final  String jobId;
@override final  String signedUrl;
@override final  int expiresIn;
 final  Map<String, String> _requiredHeaders;
@override Map<String, String> get requiredHeaders {
  if (_requiredHeaders is EqualUnmodifiableMapView) return _requiredHeaders;
  // ignore: implicit_dynamic_type
  return EqualUnmodifiableMapView(_requiredHeaders);
}


/// Create a copy of SignedUrlResponse
/// with the given fields replaced by the non-null parameter values.
@override @JsonKey(includeFromJson: false, includeToJson: false)
@pragma('vm:prefer-inline')
_$SignedUrlResponseCopyWith<_SignedUrlResponse> get copyWith => __$SignedUrlResponseCopyWithImpl<_SignedUrlResponse>(this, _$identity);

@override
Map<String, dynamic> toJson() {
  return _$SignedUrlResponseToJson(this, );
}

@override
bool operator ==(Object other) {
  return identical(this, other) || (other.runtimeType == runtimeType&&other is _SignedUrlResponse&&(identical(other.jobId, jobId) || other.jobId == jobId)&&(identical(other.signedUrl, signedUrl) || other.signedUrl == signedUrl)&&(identical(other.expiresIn, expiresIn) || other.expiresIn == expiresIn)&&const DeepCollectionEquality().equals(other._requiredHeaders, _requiredHeaders));
}

@JsonKey(includeFromJson: false, includeToJson: false)
@override
int get hashCode => Object.hash(runtimeType,jobId,signedUrl,expiresIn,const DeepCollectionEquality().hash(_requiredHeaders));

@override
String toString() {
  return 'SignedUrlResponse(jobId: $jobId, signedUrl: $signedUrl, expiresIn: $expiresIn, requiredHeaders: $requiredHeaders)';
}


}

/// @nodoc
abstract mixin class _$SignedUrlResponseCopyWith<$Res> implements $SignedUrlResponseCopyWith<$Res> {
  factory _$SignedUrlResponseCopyWith(_SignedUrlResponse value, $Res Function(_SignedUrlResponse) _then) = __$SignedUrlResponseCopyWithImpl;
@override @useResult
$Res call({
 String jobId, String signedUrl, int expiresIn, Map<String, String> requiredHeaders
});




}
/// @nodoc
class __$SignedUrlResponseCopyWithImpl<$Res>
    implements _$SignedUrlResponseCopyWith<$Res> {
  __$SignedUrlResponseCopyWithImpl(this._self, this._then);

  final _SignedUrlResponse _self;
  final $Res Function(_SignedUrlResponse) _then;

/// Create a copy of SignedUrlResponse
/// with the given fields replaced by the non-null parameter values.
@override @pragma('vm:prefer-inline') $Res call({Object? jobId = null,Object? signedUrl = null,Object? expiresIn = null,Object? requiredHeaders = null,}) {
  return _then(_SignedUrlResponse(
jobId: null == jobId ? _self.jobId : jobId // ignore: cast_nullable_to_non_nullable
as String,signedUrl: null == signedUrl ? _self.signedUrl : signedUrl // ignore: cast_nullable_to_non_nullable
as String,expiresIn: null == expiresIn ? _self.expiresIn : expiresIn // ignore: cast_nullable_to_non_nullable
as int,requiredHeaders: null == requiredHeaders ? _self._requiredHeaders : requiredHeaders // ignore: cast_nullable_to_non_nullable
as Map<String, String>,
  ));
}


}

// dart format on
