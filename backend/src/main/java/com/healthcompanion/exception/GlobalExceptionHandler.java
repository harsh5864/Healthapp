package com.healthcompanion.exception;
import java.util.*; import org.springframework.http.*; import org.springframework.web.bind.MethodArgumentNotValidException; import org.springframework.web.bind.annotation.*;
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(ApiException.class) ResponseEntity<Map<String,String>> api(ApiException e){return ResponseEntity.status(e.getStatus()).body(Map.of("code",e.getCode(),"message",e.getMessage()));}
    @ExceptionHandler(MethodArgumentNotValidException.class) ResponseEntity<Map<String,String>> validation(MethodArgumentNotValidException e){String message=e.getBindingResult().getFieldErrors().stream().findFirst().map(x->x.getField()+": "+x.getDefaultMessage()).orElse("Invalid request"); return ResponseEntity.badRequest().body(Map.of("code","VALIDATION_ERROR","message",message));}
    @ExceptionHandler(Exception.class) ResponseEntity<Map<String,String>> generic(Exception e){return ResponseEntity.status(500).body(Map.of("code","INTERNAL_ERROR","message","Something went wrong. Please try again."));}
}
