package hird.controller;


import hird.model.User;
import hird.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class UserController {
    private final UserService userService;

    public UserController(UserService userService){
        this.userService=userService;
    }

    @GetMapping("/me")
    public ResponseEntity<?> authenticatedUser(){
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        User user = (User) authentication.getPrincipal();
        return ResponseEntity.ok(user);
    }

    @GetMapping("/")
    public ResponseEntity<?> fetchAllUsers(){
        List<User> users = userService.getAllUsers();
        return ResponseEntity.ok(users);
    }
}
