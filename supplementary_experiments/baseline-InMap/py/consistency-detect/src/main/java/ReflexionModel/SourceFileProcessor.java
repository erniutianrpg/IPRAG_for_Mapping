package ReflexionModel;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.stream.Collectors;


//Later, try code summaries for methods and classes.

// Utility class for filtering and preprocessing source code files
public class SourceFileProcessor {
    private static final Pattern LINE_COMMENT = Pattern.compile("(//.*?$)|(/\\*.*?\\*/)", Pattern.MULTILINE | Pattern.DOTALL);


    // List of libraries to exclude
    private static final List<String> EXCLUSION_LIST = Arrays.asList("java", "javax", "javafx");

    // JavaList of keywords
    private static final List<String> JAVA_KEYWORDS = Arrays.asList("int ", "enum ", "switch ");

    // JavaSpecial characters in 
    private static final Pattern SPECIAL_CHARACTERS = Pattern.compile("[^a-zA-Z0-9] ");

    private static final Pattern IMPORT_STATEMENTS = Pattern.compile("^import .*;$", Pattern.MULTILINE);
    private static final Pattern PRIVATE_STATEMENTS = Pattern.compile("^private .*;$", Pattern.MULTILINE);

    //Stop words
    private static List<String> stopWords = Arrays.asList(
            "a", "an", "and", "are", "as", "at", "be", "but", "by",
            "for", "if", "in", "into", "is", "it",
            "no", "not", "of", "on", "or", "such",
            "that", "the", "their", "then", "there", "these",
            "they", "this", "to", "was", "will", "with", "which"
    );

    // Filter files
    public static boolean shouldIncludeFile(String fileName) {
        for (String exclusion : EXCLUSION_LIST) {
            if (fileName.startsWith(exclusion)) {
                return false;
            }
        }

        return true;
    }

    // Preprocess file
    public static String preprocessFile(String filePath) throws IOException {

        String content = Files.readString(Paths.get(filePath));

        // Split the content into code and comment sections
        String comments = getComments(content);
        String code = getCode(content);

        // removeimportandprivatestatement
        code = removeImportAndPrivateStatements(code);

        // Remove keywords
        code = removeKeywords(code);

        // Remove special characters
        code = code.replaceAll("[^a-zA-Z0-9] "," ");
        comments = comments.replaceAll("[^a-zA-Z0-9] "," ");


        comments=Arrays.stream(comments.split(" "))
                .filter(word -> !stopWords.contains(word))
                .collect(Collectors.joining(" "));
        // Save the cleaned words
        String cleanedTokens = code + " " + comments;

        return cleanedTokens;
    }

    // removeimportandprivatestatement
    private static String removeImportAndPrivateStatements(String code) {
        // deleteimportstatement
        code = IMPORT_STATEMENTS.matcher(code).replaceAll("");
        // deleteprivatestatement
        code = PRIVATE_STATEMENTS.matcher(code).replaceAll("");
        return code;
    }

    // Remove keywords
    private static String removeKeywords(String code) {
        for (String keyword : JAVA_KEYWORDS) {
            code = code.replace(keyword, "");
        }

        return code;
    }

    public static String getComments(String content) {
        StringBuilder comments = new StringBuilder();

        // Find all comments
        Matcher matcher = LINE_COMMENT.matcher(content);
        while (matcher.find()) {
            comments.append(matcher.group()).append("\n");
        }


        return comments.toString();
    }

    public static String getCode(String content) {
        // Remove all single-line and multi-line comments
        content = LINE_COMMENT.matcher(content).replaceAll("");

        return content;
    }
}

