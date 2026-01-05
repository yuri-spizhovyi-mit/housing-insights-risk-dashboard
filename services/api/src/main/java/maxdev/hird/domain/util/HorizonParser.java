package maxdev.hird.domain.util;

public final class HorizonParser {

    private HorizonParser() {}

    public static int toMonths(String horizon) {
        return switch (horizon) {
            case "1y" -> 12;
            case "2y" -> 24;
            case "5y" -> 60;
            case "10y" -> 120;
            default -> throw new IllegalArgumentException("Invalid horizon");
        };
    }
}

