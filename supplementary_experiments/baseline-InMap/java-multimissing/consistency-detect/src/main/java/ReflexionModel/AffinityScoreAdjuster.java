package ReflexionModel;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Locale;
import java.util.Set;
import java.util.HashSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class AffinityScoreAdjuster {

    // Function to adjust the document module affinity score
    public static BigDecimal adjustAffinityScore(BigDecimal originalScore, BigDecimal mnBoostFactor, String className, String moduleName,String project) {
        Set<String> classWords = new HashSet<>();

        // Split by slash className
        String[] classNameParts = className.replaceAll("\\.\\w+$", "").split("/");

// Find the position of the last specified keyword
        int startIndex = 0;
        for (int i = 0; i < classNameParts.length; i++) {
            String part = classNameParts[i].toLowerCase();
            if (part.equals("src") ||part.equals("test") || part.equals("main") || part.equals("sources") || part.equals("org")|| part.equals(project)) {
                startIndex = i + 1; // Record the index immediately after the last keyword position
            }
        }

// Start recording after the last keyword
        for (int i = startIndex; i < classNameParts.length; i++) {
            String processedPart = classNameParts[i].toLowerCase();
            classWords.add(processedPart);
        }
//        for (String part : classNameParts) {
//            // remove .suffix and convert to lowercase
//            String processedPart = part.toLowerCase();
//            classWords.add(processedPart);
//        }
        Set<String> moduleWords = splitWords(moduleName);
        if (classWords.contains("bezierpathiterator") ){
            int flag=1;
        }

        // Check if there is a common keyword between class name and module name
        boolean hasCommonKeyword = containsCommonKeyword(classWords, moduleWords);

        BigDecimal documentModuleAffinityScore = originalScore;
        if (hasCommonKeyword) {
            // If there is a common keyword, multiply the score by mnBoostFactor
            documentModuleAffinityScore = documentModuleAffinityScore.multiply(mnBoostFactor);
        }

        return documentModuleAffinityScore;
    }

    // Function to split CamelCase or words separated by non-word characters
    private static Set<String> splitWords(String input) {
        Set<String> words = new HashSet<>();

        // Step 1:Split by non-word characters
        String[] tokens = input.split("\\W+");

        // Step 2:Process each token
        for (String token : tokens) {
            if (token.isEmpty()) {
                continue;
            }

            Matcher matcher = Pattern.compile(
                    "[A-Z][a-z0-9]*" +                // Match a word that starts with an uppercase letter
                            "(?:[A-Z][a-z0-9]*)*" +           // followed by zero or more words starting with an uppercase letter (used to handle consecutive uppercase letters)
                            "|[a-z0-9]+"                      // or a word composed entirely of lowercase letters or digits
            ).matcher(token);

            while (matcher.find()) {
                String word = matcher.group();
                if (!word.isEmpty()) {
                    words.add(word.toLowerCase(Locale.ROOT));
                }
            }
        }
        return words;
    }




    private static boolean containsCommonKeyword(Set<String> classWords, Set<String> moduleWords) {
        for (String classWord : classWords) {
            for (String moduleWord : moduleWords) {
                if (classWord.contains(moduleWord) || moduleWord.contains(classWord)) {
                    return true; // If either word contains the other, return  true
                }
            }
        }
        return false;
    }



}

