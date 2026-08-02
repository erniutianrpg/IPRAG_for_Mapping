import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Locale;
import java.util.Set;
import java.util.HashSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class ModuleAffinityTest {

    // Function to split CamelCase or words separated by non-word characters
    private static Set<String> splitWords(String input) {
        Set<String> words = new HashSet<>();

        // Step 1: Split by non-word characters
        String[] tokens = input.split("\\W+");

        // Step 2: Split CamelCase in each token
        for (String token : tokens) {
            Matcher matcher = Pattern.compile("[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)").matcher(token);
            while (matcher.find()) {
                String word = matcher.group().toLowerCase(Locale.ROOT);
                words.add(word);
            }
        }
        return words;
    }

    // Function to check if there is a common keyword between two sets of words
    private static boolean containsCommonKeyword(Set<String> classWords, Set<String> moduleWords) {
        for (String classWord : classWords) {
            if (moduleWords.contains(classWord)) {
                return true; // Return true if any common word is found
            }
        }
        return false;
    }

    public static void main(String[] args) {
        // Example class names and module names
        String className = "ImageProvider";
        String moduleName = "Image Scene";

        // Split class and module names into words
        Set<String> classWords = splitWords(className);
        Set<String> moduleWords = splitWords(moduleName);

        // Example document module affinity score and boost factor
        BigDecimal documentModuleAffinityScore = new BigDecimal("1.00");
        BigDecimal mnBoostFactor = new BigDecimal("1.50");

        // Adjust affinity score based on the presence of common keywords
        if (containsCommonKeyword(classWords, moduleWords)) {
            documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
            System.out.println("Boosted Score: " + documentModuleAffinityScore);
        } else {
            if (mnBoostFactor.compareTo(BigDecimal.valueOf(0.00)) != 0) {
                documentModuleAffinityScore = documentModuleAffinityScore.divide(mnBoostFactor, 20, RoundingMode.HALF_UP);
                System.out.println("Reduced Score: " + documentModuleAffinityScore);
            } else {
                documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
                System.out.println("Unchanged Score: " + documentModuleAffinityScore);
            }
        }
    }
}
