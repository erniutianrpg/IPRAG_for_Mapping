package ReflexionModel;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.Stack;
import java.util.regex.Pattern;

public class PreProcessing
{
    final String stopWords [] = { "a", "able", "about", "after", "all", "almost", "also", "am", "among", "an", "and", "are", "as", "at", "be", "because",
            "been", "but", "by", "can", "could", "dear", "did", "do", "does", "else", "ever", "for", "from", "get", "got", "had", "has",
            "have", "he", "her", "hers", "him", "his", "how", "however", "i", "if", "in", "into", "is", "it", "its", "just", "let", "like", "me",
            "more", "my", "neither", "no", "nor", "of", "off", "on", "or", "other", "our", "own", "rather", "said", "say", "says",
            "she", "should", "since", "so", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "tis", "to", "too", "twas", "us",
            "wants", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet", "you", "your" };

    final String javaKeyWords [] = { "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
            "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float", "for", "if", "goto",
            "implements", "import", "instanceof", "int", "interface", "long", "native", "new", "package", "private", "protected",
            "public", "return", "short", "static", "strictfp", "string", "super", "switch", "synchronized", "this", "throw", "throws",
            "transient", "try", "void", "volatile", "while", "true", "false", "null", "var", "const", "goto", "@Override",
            "@SuppressWarnings", "@Retention", "@Documented", "@Target", "@Inherited", "@SafeVarargs", "@FunctionalInterface",
            "@Repeatable", "@param", "@author", ".INSTANCE" };

    final String pythonKeyWords [] = { "false", "none", "true", "and", "as", "assert", "async", "await", "break", "class",
            "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import",
            "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
            "self", "cls" };

    final String chars [] = { "\\{", "\\}", "\\[", "\\]", "\\(", "\\)", ";", "\\*", "/", "\\+", "&", "@", "\\|", "<", ">",
            "=", ":", ",", "\"", "'", "\\.", "!", "_" };

    final Set<String> ignoredPythonDirs = new HashSet<>(Arrays.asList(
            ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", ".venv", "venv", "env",
            "site-packages", "build", "dist"
    ));

    File folder;
    String programSources;
    String sourceFileExt;
    String sourceCodeExt;
    String language;
    ArrayList<File> systemFiles = new ArrayList<File>();

    public PreProcessing(String programSources,String sourceFileExt) {
        this(programSources, sourceFileExt, "java");
    }

    public PreProcessing(String programSources,String sourceFileExt, String language) {
        this.programSources = programSources;
        this.folder = new File(programSources);
        this.sourceFileExt = sourceFileExt;
        this.language = normalizeLanguage(language);
        this.sourceCodeExt = this.language.equals("python") ? ".py" : ".java";
        this.systemFiles = create(programSources);
    }

    private ArrayList<File> create(String programSources) {
        ArrayList<File> files = new ArrayList<File>();
        File directory = new File(programSources);
        Stack<File> stack = new Stack<File>();
        stack.push(directory);

        while (!stack.isEmpty()) {
            File current = stack.pop();

            if (current.isDirectory()) {
                if (language.equals("python") && ignoredPythonDirs.contains(current.getName())) {
                    continue;
                }
                File[] childFiles = current.listFiles();
                if (childFiles == null) {
                    continue;
                }
                for (File file : childFiles) {
                    stack.push(file);
                }
            }
            else if (current.isFile() && current.getName().endsWith(sourceCodeExt)) {
                files.add(current);
            }
        }

        return files;
    }

    private void delteOldSourceFiles()
    {
        Stack<File> stack = new Stack<File>();
        stack.push( folder );

        while( !stack.isEmpty() )
        {
            File childFolder = stack.pop();
            File[] files = childFolder.listFiles();
            if (files == null) {
                continue;
            }

            for( File file : files )
            {
                if( file.isFile() && file.getPath().endsWith( sourceFileExt ) )
                {
                    file.delete();
                }
                else if( file.isDirectory() )
                {
                    stack.push( file );
                }
            }
        }
    }

    public void cleanSourceFiles(List<String> exclusionList)
    {
        delteOldSourceFiles();
        for( File file : systemFiles )
        {
            if (!Correctfilepath(file.toString(), exclusionList)) {
                continue;
            }

            String progSrcs = programSources.replace("\\", ".").replace("/", ".");
            String sourceName = file.toString().replace("\\", ".").replace("/", ".");
            sourceName = sourceName.replace(progSrcs, "");
            sourceName = sourceName.replaceAll( Pattern.quote(sourceCodeExt) + "$", "" );

            try
            {
                String content = readSourceFile(file);
                String cleanedSource = cleanSource(content, sourceName);

                String stripedFile = file.getPath();
                stripedFile = stripedFile.replaceAll( Pattern.quote(sourceCodeExt) + "$", sourceFileExt );
                File cleanedFile = new File( stripedFile );
                BufferedWriter writeOut = new BufferedWriter( new FileWriter( cleanedFile, true ) );
                writeOut.append( cleanedSource );
                writeOut.close();
            }
            catch( IOException e )
            {
                e.printStackTrace();
            }
        }
    }

    private boolean Correctfilepath(String filePath, List<String> exclusionList) {
        if (!filePath.endsWith(sourceCodeExt)) {
            return false;
        }
        if (exclusionList == null || exclusionList.isEmpty()) {
            return true;
        }

        Path path = Paths.get(filePath);
        String[] parts = path.toString().split("[/\\\\]");

        int startIndex = -1;
        for (int i = parts.length - 1; i >= 0; i--) {
            if (parts[i].equals("src") || parts[i].equals("main") || parts[i].equals("sources") || parts[i].equals("org") || parts[i].equals("archstudio")) {
                startIndex = i + 1;
                break;
            }
        }
        if (startIndex == -1) {
            if (language.equals("python")) {
                startIndex = 0;
            } else {
                return false;
            }
        }

        for (int endIndex = parts.length - 1; endIndex >= startIndex; endIndex--) {
            String[] subArray = Arrays.copyOfRange(parts, startIndex, endIndex + 1);
            if (subArray.length > 0) {
                subArray[subArray.length - 1] = subArray[subArray.length - 1].replaceAll(Pattern.quote(sourceCodeExt) + "$", "");
            }
            String potentialModule = String.join(".", subArray);
            if (exclusionList.contains(potentialModule)){
                return false;
            }
        }

        return true;
    }

    private String cleanSource(String content, String sourceName) {
        String codeOnly = language.equals("python") ? cleanPythonSource(content) : cleanJavaSource(content);
        codeOnly = codeOnly.toLowerCase();
        sourceName = sourceName.toLowerCase();

        for( int j = 0; j < chars.length; j++ )
        {
            codeOnly = codeOnly.replaceAll( chars[ j ].toLowerCase(), " " );
            sourceName = sourceName.replaceAll( chars[ j ].toLowerCase(), " " );
        }

        String[] keywords = language.equals("python") ? pythonKeyWords : javaKeyWords;
        for( int j = 0; j < keywords.length; j++ )
        {
            codeOnly = codeOnly.replaceAll( "\\W+" + Pattern.quote(keywords[ j ].toLowerCase()) + "\\W+", " " );
        }
        for( int j = 0; j < stopWords.length; j++ )
        {
            codeOnly = codeOnly.replaceAll( "\\W+" + stopWords[ j ].toLowerCase() + "\\W+", " " );
        }

        return codeOnly + " " + sourceName;
    }

    private String cleanJavaSource(String content) {
        String[] lines = content.split("\\R");
        String commentsRegex = "((/\\*+)|(//)).*";
        StringBuilder codeOnly = new StringBuilder();
        boolean longComment = false;

        for (String line : lines) {
            line = line.replaceAll( "^(\\s)*import(.*);" , " " );
            line = line.replaceAll( "^(\\s)*private(.*);" , " " );
            if( !longComment )
            {
                String code = line.replaceAll( commentsRegex , " " );
                codeOnly.append(" \n").append(code);
                String trimmed = line.trim();
                if( trimmed.contains( "/*" ) && !trimmed.contains( "*/" ) )
                {
                    longComment = true;
                }
            }
            else if( line.contains( "*/" ) )
            {
                longComment = false;
            }
        }

        return codeOnly.toString();
    }

    private String cleanPythonSource(String content) {
        String code = content.replaceAll("(?s)'''(.*?)'''|\"\"\"(.*?)\"\"\"", " ");
        code = code.replaceAll("(?m)^\\s*(from\\s+\\S+\\s+import|import\\s+).*$", " ");
        code = code.replaceAll("(?m)#.*$", " ");
        return code;
    }

    private String readSourceFile(File file) throws IOException {
        try {
            return Files.readString(file.toPath(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            BufferedReader bufferedReader = new BufferedReader( new InputStreamReader( new FileInputStream( file ), "ISO-8859-1") );
            StringBuilder content = new StringBuilder();
            String line;
            while ((line = bufferedReader.readLine()) != null) {
                content.append(line).append("\n");
            }
            bufferedReader.close();
            return content.toString();
        }
    }

    private String normalizeLanguage(String language) {
        if (language == null) {
            return "java";
        }
        String normalized = language.trim().toLowerCase();
        if (normalized.equals("py") || normalized.equals("python")) {
            return "python";
        }
        return "java";
    }
}
