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

    final String cppKeyWords [] = { "alignas", "alignof", "and", "and_eq", "asm", "auto", "bitand", "bitor", "bool",
            "break", "case", "catch", "char", "char8_t", "char16_t", "char32_t", "class", "compl", "concept", "const",
            "consteval", "constexpr", "constinit", "const_cast", "continue", "co_await", "co_return", "co_yield",
            "decltype", "default", "delete", "do", "double", "dynamic_cast", "else", "enum", "explicit", "export",
            "extern", "false", "float", "for", "friend", "goto", "if", "inline", "int", "long", "mutable",
            "namespace", "new", "noexcept", "not", "not_eq", "nullptr", "operator", "or", "or_eq", "private",
            "protected", "public", "register", "reinterpret_cast", "requires", "return", "short", "signed", "sizeof",
            "static", "static_assert", "static_cast", "struct", "switch", "template", "this", "thread_local", "throw",
            "true", "try", "typedef", "typeid", "typename", "union", "unsigned", "using", "virtual", "void",
            "volatile", "wchar_t", "while", "xor", "xor_eq", "define", "elif", "endif", "error", "ifdef", "ifndef",
            "include", "line", "pragma", "undef" };

    final String chars [] = { "\\{", "\\}", "\\[", "\\]", "\\(", "\\)", ";", "\\*", "/", "\\+", "&", "@", "\\|", "<", ">",
            "=", ":", ",", "\"", "'", "\\.", "!", "_", "#", "~", "\\?", "%", "\\$", "\\\\" };

    final Set<String> ignoredDirs = new HashSet<>(Arrays.asList(
            ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", ".venv", "venv", "env",
            "site-packages", "build", "dist", "target", "out", "bin", "obj", "CMakeFiles", "cmake-build-debug",
            "cmake-build-release", ".vs", ".vscode"
    ));

    File folder;
    String programSources;
    String sourceFileExt;
    List<String> sourceCodeExts;
    String language;
    ArrayList<File> systemFiles = new ArrayList<File>();

    public PreProcessing(String programSources,String sourceFileExt) {
        this(programSources, sourceFileExt, "cpp");
    }

    public PreProcessing(String programSources,String sourceFileExt, String language) {
        this.programSources = programSources;
        this.folder = new File(programSources);
        this.sourceFileExt = sourceFileExt;
        this.language = normalizeLanguage(language);
        this.sourceCodeExts = getSourceCodeExts(this.language);
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
                if (ignoredDirs.contains(current.getName())) {
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
            else if (current.isFile() && isSourceFile(current.getName())) {
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
            sourceName = removeSourceExtension(sourceName);

            try
            {
                String content = readSourceFile(file);
                String cleanedSource = cleanSource(content, sourceName);

                String stripedFile = getProcessedFilePath(file);
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
        if (!isSourceFile(filePath)) {
            return false;
        }
        if (exclusionList == null || exclusionList.isEmpty()) {
            return true;
        }

        Path path = Paths.get(filePath);
        String[] parts = path.toString().split("[/\\\\]");

        int startIndex = -1;
        for (int i = parts.length - 1; i >= 0; i--) {
            if (parts[i].equals("src") || parts[i].equals("main") || parts[i].equals("source") || parts[i].equals("sources")
                    || parts[i].equals("include") || parts[i].equals("inc") || parts[i].equals("lib")
                    || parts[i].equals("org") || parts[i].equals("archstudio")) {
                startIndex = i + 1;
                break;
            }
        }
        if (startIndex == -1) {
            if (language.equals("python") || language.equals("cpp")) {
                startIndex = 0;
            } else {
                return false;
            }
        }

        for (int endIndex = parts.length - 1; endIndex >= startIndex; endIndex--) {
            String[] subArray = Arrays.copyOfRange(parts, startIndex, endIndex + 1);
            if (subArray.length > 0) {
                subArray[subArray.length - 1] = removeSourceExtension(subArray[subArray.length - 1]);
            }
            String potentialModule = String.join(".", subArray);
            if (exclusionList.contains(potentialModule)){
                return false;
            }
        }

        return true;
    }

    private String cleanSource(String content, String sourceName) {
        String codeOnly;
        if (language.equals("python")) {
            codeOnly = cleanPythonSource(content);
        } else if (language.equals("cpp")) {
            codeOnly = cleanCppSource(content);
        } else {
            codeOnly = cleanJavaSource(content);
        }
        codeOnly = codeOnly.toLowerCase();
        sourceName = sourceName.toLowerCase();

        for( int j = 0; j < chars.length; j++ )
        {
            codeOnly = codeOnly.replaceAll( chars[ j ].toLowerCase(), " " );
            sourceName = sourceName.replaceAll( chars[ j ].toLowerCase(), " " );
        }

        String[] keywords = getLanguageKeywords();
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

    private String cleanCppSource(String content) {
        String[] lines = content.split("\\R");
        StringBuilder codeOnly = new StringBuilder();
        boolean longComment = false;

        for (String line : lines) {
            line = line.replaceAll("^\\s*#\\s*(include|define|ifdef|ifndef|endif|pragma|undef|if|elif|else|error|line).*$", " ");
            if (!longComment) {
                String code = line.replaceAll("//.*", " ");
                int blockStart = code.indexOf("/*");
                while (blockStart >= 0) {
                    int blockEnd = code.indexOf("*/", blockStart + 2);
                    if (blockEnd >= 0) {
                        code = code.substring(0, blockStart) + " " + code.substring(blockEnd + 2);
                        blockStart = code.indexOf("/*");
                    } else {
                        code = code.substring(0, blockStart);
                        longComment = true;
                        break;
                    }
                }
                codeOnly.append(" \n").append(code);
            } else {
                int blockEnd = line.indexOf("*/");
                if (blockEnd >= 0) {
                    longComment = false;
                    codeOnly.append(" \n").append(line.substring(blockEnd + 2).replaceAll("//.*", " "));
                }
            }
        }

        return codeOnly.toString();
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
            return "cpp";
        }
        String normalized = language.trim().toLowerCase();
        if (normalized.equals("py") || normalized.equals("python")) {
            return "python";
        }
        if (normalized.equals("c") || normalized.equals("cc") || normalized.equals("cpp")
                || normalized.equals("cxx") || normalized.equals("c++")) {
            return "cpp";
        }
        return "java";
    }

    private List<String> getSourceCodeExts(String language) {
        if (language.equals("python")) {
            return Arrays.asList(".py");
        }
        if (language.equals("cpp")) {
            return Arrays.asList(".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx");
        }
        return Arrays.asList(".java");
    }

    private boolean isSourceFile(String path) {
        String lowerPath = path.toLowerCase();
        for (String ext : sourceCodeExts) {
            if (lowerPath.endsWith(ext)) {
                return true;
            }
        }
        return false;
    }

    private String removeSourceExtension(String path) {
        for (String ext : sourceCodeExts) {
            if (path.toLowerCase().endsWith(ext)) {
                return path.substring(0, path.length() - ext.length());
            }
        }
        return path;
    }

    private String getProcessedFilePath(File file) {
        String filePath = file.getPath();
        if (language.equals("cpp")) {
            return filePath + sourceFileExt;
        }
        return removeSourceExtension(filePath) + sourceFileExt;
    }

    private String[] getLanguageKeywords() {
        if (language.equals("python")) {
            return pythonKeyWords;
        }
        if (language.equals("cpp")) {
            return cppKeyWords;
        }
        return javaKeyWords;
    }
}
