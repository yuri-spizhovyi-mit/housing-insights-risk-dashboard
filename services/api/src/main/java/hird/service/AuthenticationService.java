package hird.service;

import hird.dto.LoginUserDto;
import hird.dto.VerifyUserDto;
import hird.exceptions.ResourceNotFoundException;
import hird.model.User;
import java.time.LocalDateTime;
import java.util.Optional;
import java.util.Random;

import hird.dto.RegisterUserDto;
import hird.repository.UserRepository;
import jakarta.mail.MessagingException;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class AuthenticationService {
    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final AuthenticationManager authenticationManager;
    private final EmailService emailService;

    public AuthenticationService(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            AuthenticationManager authenticationManager,
            EmailService emailService
    ){
      this.userRepository = userRepository;
      this.passwordEncoder = passwordEncoder;
      this.authenticationManager = authenticationManager;
      this.emailService = emailService;
    }


    public User signup(RegisterUserDto userDto){
        User user = new User(userDto.username(), userDto.email(), passwordEncoder.encode(userDto.password()));

        user.setVerificationCode(generateVerificationCode());
        user.setVerificationCodeExpiredAt(LocalDateTime.now().plusMinutes(15));
        user.setEnabled(false);

        sendVerificationEmail(user);
        return userRepository.save(user);
    }

    public User authenticate(LoginUserDto userDto){
        User user = userRepository.findByEmail(userDto.email())
                .orElseThrow(() -> new ResourceNotFoundException("User not found"));

        if(!user.isEnabled())
            throw new ResourceNotFoundException("Account is not verified");

        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        user.getUsername(),
                        user.getPassword()
                )
        );

        return user;
    }

    public void verifyUser(VerifyUserDto verifyUserDto){
        Optional<User> optionalUser = userRepository.findByEmail(verifyUserDto.email());

        if(optionalUser.isPresent()){
            User user = optionalUser.get();

            if(user.getVerificationCodeExpiredAt().isBefore(LocalDateTime.now()))
                throw new RuntimeException("Verification code has been expired");

            if(user.getVerificationCode().equals(user.getVerificationCode())){
                user.setEnabled(true);
                user.setVerificationCode(null);
                user.setVerificationCodeExpiredAt(null);
                userRepository.save(user);
            } else {
                throw new RuntimeException("Invalid verification code");
            }
        } else {
            throw new ResourceNotFoundException("User not found");
        }
    }

    public void resendVerificationCode(String email){
        Optional<User> optionalUser = userRepository.findByEmail(email);

        if(optionalUser.isPresent()){
            User user = optionalUser.get();

            if(user.isEnabled())
                throw new RuntimeException("Account is already verified");

            user.setVerificationCode(generateVerificationCode());
            user.setVerificationCodeExpiredAt(LocalDateTime.now().plusMinutes(15));
            user.setEnabled(false);

            sendVerificationEmail(user);
            userRepository.save(user);
        } else {
            throw new ResourceNotFoundException("User not found");
        }
    }

    public void sendVerificationEmail(User user){
        String subject = "Account verification";
        String verificationCode = user.getVerificationCode();
        String htmlMessage = """
         <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="background-color: #f5f5f5; padding: 20px;">
                    <h2 style="color: #333;">Welcome to our app!</h2>
                    <p style="font-size: 16px;">Please enter the verification code below to continue:</p>
                    <div style="background-color: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                        <h3 style="color: #333;">Verification Code:</h3>
                        <p style="font-size: 18px; font-weight: bold; color: #007bff;">%s</p>
                    </div>
                </div>
            </body>
        </html>
        """;

         try{
             emailService.sendVerificationEmail(subject, verificationCode, htmlMessage);
         } catch (MessagingException e){
             e.printStackTrace();
         }
    }

    private String generateVerificationCode(){
        Random random = new Random();
        int code = random.nextInt(900000) + 100000;
        return String.valueOf(code);
    }
}
