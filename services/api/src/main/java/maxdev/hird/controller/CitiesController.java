package maxdev.hird.controller;

import maxdev.hird.service.CitiesService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/cities")
public class CitiesController {
    private final CitiesService citiesService;

    public CitiesController(CitiesService citiesService){
        this.citiesService = citiesService;
    }

    @GetMapping
    public ResponseEntity<List<String>> getCities(){
        List<String> cities = citiesService.retrieveCities();
        return ResponseEntity.ok(cities);
    }
}
