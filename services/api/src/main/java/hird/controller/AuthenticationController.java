package hird.controller;

import hird.dto.LoginUserDto;
import hird.dto.RegisterUserDto;
import hird.dto.VerifyUserDto;
import hird.model.User;
import hird.responses.LoginResponse;
import hird.service.AuthenticationService;
import hird.service.JwtHelper;
import hird.service.JwtService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/auth/")
public class AuthenticationController {
    private final AuthenticationService authenticationService;
    private final JwtHelper jwtService;

    public AuthenticationController(AuthenticationService authenticationService, JwtService jwtService){
        this.authenticationService=authenticationService;
        this.jwtService = jwtService;
    }

    @PostMapping("/signup")
    public ResponseEntity<?> register(@RequestBody RegisterUserDto userDto){
        User user = authenticationService.signup(userDto);
        return ResponseEntity.ok(user);
    }

    @GetMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginUserDto userDto){
        User user = authenticationService.authenticate(userDto);
        String jwrToken = jwtService.generateToken(user);
        LoginResponse response = new LoginResponse(jwrToken, jwtService.getJwtExpirationMilliseconds());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/verify")
    public ResponseEntity<?> verify(@RequestBody VerifyUserDto userDto){
        authenticationService.verifyUser(userDto);
        return ResponseEntity.ok("Account verified successfully!");
    }

    @PostMapping("/resend")
    public ResponseEntity<?> resendVerificationCode(@RequestParam String email){
        authenticationService.resendVerificationCode(email);
        return ResponseEntity.ok("Verification code sent");
    }
}
