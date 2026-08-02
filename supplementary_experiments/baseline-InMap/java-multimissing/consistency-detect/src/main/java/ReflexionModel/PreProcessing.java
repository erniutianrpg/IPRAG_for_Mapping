/*Author: Zipani Tom Sinkala (tom.sinkala@kau.se)
 *
 */

package ReflexionModel;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.FileInputStream;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;



public class PreProcessing
{
    final String stopWords [] = { "a", "able", "about", "after", "all", "almost", "also", "am", "among", "an", "and", "are", "as", "at", "be", "because",
            "been", "but", "by", "can", "could", "dear", "did", "do", "does", "else", "ever", "for", "from", "get", "got", "had", "has",
            "have", "he", "her", "hers", "him", "his", "how", "however", "i", "if", "in", "into", "is", "it", "its", "just", "let", "like", "me",
            "more", "my", "neither", "no", "nor", "of", "off", "on", "or", "other", "our", "own", "rather", "said", "say", "says",
            "she", "should", "since", "so", "such", "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "tis", "to", "too", "twas", "us",
            "wants", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with", "would", "yet", "you", "your" };

    final String methodPrefixes [] = { "get", "set", "init", "is", "has", "from", "can", "show", "hide", "update", "create", "find", "add", "start", "as", "add",
            "end", "close", "open", "next" }; //

    // taken from https://en.wikipedia.org/wiki/List_of_Java_keywords and https://en.wikipedia.org/wiki/Java_annotation
    final String javaKeyWords [] = { "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
            "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float", "for", "if", "goto",
            "implements", "import", "instanceof", "int", "interface", "long", "native", "new", "package", "private", "protected",
            "public", "return", "short", "static", "strictfp", "string", "super", "switch", "synchronized", "this", "throw", "throws",
            "transient", "try", "void", "volatile", "while", "true", "false", "null", "var", "const", "goto", "@Override",
            "@SuppressWarnings", "@Retention", "@Documented", "@Target", "@Inherited", "@SafeVarargs", "@FunctionalInterface",
            "@Repeatable", "@param", "@author", ".INSTANCE" };

    final String chars [] = { "\\{", "\\}", "\\[", "\\]", "\\(", "\\)", ";", "\\*", "/", "\\+", "&", "@", "\\|", "<", ">",
            "=", ":", ",", "\"", "\\.", "!" };

    File folder;
    String programSources;
    String sourceFileExt;
    ArrayList<File> systemFiles = new ArrayList<File>();

    // Modified constructor
    public PreProcessing(String programSources,String sourceFileExt) {
        this.programSources = programSources;
        this.folder = new File(programSources);
        this.sourceFileExt = sourceFileExt;
        this.systemFiles = create(programSources);  // Directly set  systemFiles to the passed-in  files
    }

    private ArrayList<File> create(String programSources) {
        // Create a new  ArrayList object to store  File object
        ArrayList<File> files = new ArrayList<File>();

        // Create a  File object to represent this directory
        File directory = new File(programSources);

        // Create a stack to process the directory structure
        Stack<File> stack = new Stack<File>();
        stack.push(directory);

        // When the stack is not empty, continue processing directories and files
        while (!stack.isEmpty()) {
            File current = stack.pop();

            // If the current path is a directory, add all of its subdirectories and files to the stack
            if (current.isDirectory()) {
                for (File file : current.listFiles()) {
                    stack.push(file);
                }
            }
            // If the current path is a file and the extension is  .java,then add it to  ArrayList
            else if (current.isFile() && current.getName().endsWith(".java")) {
                files.add(current);
            }
        }

        return files;
    }

    private void delteOldSourceFiles()
    {
        // delete pre-processed files

        Stack<File> stack = new Stack<File>();
        stack.push( folder );

        while( !stack.isEmpty() )
        {
            File childFolder = stack.pop();
            File[] files = childFolder.listFiles();
            ArrayList<File> filesList = new ArrayList<File>();

            for( int j = 0; j < files.length; j++ )
            {
                filesList.add( files[ j ] );
            }

            for( File file : filesList )
            {
                if( file.isFile() && file.getPath().contains( sourceFileExt ) )
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
        delteOldSourceFiles();				// delete all existing pre-processed files before cleaning
        // clean files
        for( File file : systemFiles )
        {
            if (!Correctfilepath(file.toString(), exclusionList)) {
                continue;
            }
            String progSrcs = programSources.toString().replaceAll( "/", "." );
            String className = file.toString().replaceAll( "\\\\", "." );
            className = className.toString().replaceAll( progSrcs, "" );
            className = className.toString().replaceAll( ".java", "" );

            try
            {
                // extract code and comments from file separately and clean them
                BufferedReader bufferedReader = new BufferedReader( new InputStreamReader( new FileInputStream( file ), "ISO-8859-1") );
                String commentsRegex = "((/\\*+)|(//)).*";
                Pattern commentsPattern = Pattern.compile( commentsRegex );
                String comments = "";
                String code = "";
                String codeOnly = "";
                String line = null;
                boolean longComment = false;

                while( ( line = bufferedReader.readLine() ) != null )
                {
                    // remove import statements
                    line = line.replaceAll( "^(\\s)*import(.*);" , " " );

                    // remove private statements: intended to remove private method names to exclude them from searches
                    line = line.replaceAll( "^(\\s)*private(.*);" , " " );

                    code = line;

                    // split code and comments
                    if( !longComment )
                    {
                        code = code.replaceAll( commentsRegex , " " );
                        codeOnly = codeOnly + " \n" + code;
                        Matcher matcher = commentsPattern.matcher( line );

                        if( matcher.find( ) )
                        {
                            comments = comments + " \n" + matcher.group( 0 ).toString();

                            if( matcher.group( 0 ).toString().contains( "/*" ) )
                            {
                                longComment = true;
                            }

                            if( matcher.group( 0 ).toString().contains( "*/" ) )
                            {
                                longComment = false;
                            }
                        }
                    }
                    else
                    {
                        comments = comments + " \n" + line;

                        if( line.contains( "*/" ) )
                        {
                            longComment = false;
                        }
                    }
                }

                // split code and comments
                comments = comments.toLowerCase();
                codeOnly = codeOnly.toLowerCase();

                // remove chars from comments and code
                for( int j = 0; j < chars.length; j++ )
                {
                    comments = comments.replaceAll( chars[ j ].toLowerCase(), " " );
                    codeOnly = codeOnly.replaceAll( chars[ j ].toLowerCase(), " " );
                    className = className.replaceAll( chars[ j ].toLowerCase(), " " );
                }

                // remove stop words from comments
                for( int j = 0; j < stopWords.length; j++ )
                {
                    comments = comments.replaceAll( "\\W+" + stopWords[ j ].toLowerCase() + "\\W+", " " );
                }
                // remove keywords from code
                for( int j = 0; j < javaKeyWords.length; j++ )
                {
                    codeOnly = codeOnly.replaceAll( "\\W+" + javaKeyWords[ j ].toLowerCase() + "\\W+", " " );
                }

                comments = comments + className;
                codeOnly = codeOnly + className;// adding full name of class to preserve important keywords in the package name

                bufferedReader.close();

//                String cleanedSource = className.replaceAll( ".", " " )+comments + codeOnly;
//                String cleanedSource = comments + codeOnly;			// comments & code
                String cleanedSource = codeOnly;					// code only
                //String cleanedSource = comments;					// comments only

                // remove method prefixes from code and comments
                /*for( int j = 0; j < methodPrefixes.length; j++ )
			    {
                	String methodPrefixRegex = "(^|\\s+)(" + methodPrefixes[ j ].toLowerCase() + ")\\w+";
                	Pattern methodPrefixPattern = Pattern.compile( methodPrefixRegex );
                	Matcher methodPrefixMatcher = methodPrefixPattern.matcher( cleanedSource );

                	if( methodPrefixMatcher.find( ) )
            	    {
                		cleanedSource = cleanedSource.replaceAll( methodPrefixMatcher.group( 2 ).toString(), " " );
            	    }
			    }*/

                String stripedFile = file.getPath();
                stripedFile = stripedFile.replaceAll( ".java$", sourceFileExt );
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
        if (!filePath.endsWith(".java")) {
            return false;
        }

        Path path = Paths.get(filePath);
        String[] parts = path.toString().split("[/\\\\]");
        // Use the system path separator
//        String[] parts = filePathWithoutExtension.split("\\" + File.separator);

//        String[] parts = filePath.replaceAll(".java","").split("\\");  // split by backslash

        // Start from the index where 'src' or 'main' is located
         int startIndex = -1;
        for (int i = parts.length - 1; i >= 0; i--) {
            if (parts[i].equals("src") || parts[i].equals("main") || parts[i].equals("sources")|| parts[i].equals("org") || parts[i].equals("archstudio")) {
                startIndex = i + 1;
                break;
            }
        }
        if (startIndex == -1) {
            return false; // 'src' or 'main' not found
        }

        for (int endIndex = parts.length - 1; endIndex >= startIndex; endIndex--) {
            String[] subArray = Arrays.copyOfRange(parts, startIndex, endIndex + 1);
            String potentialModule = String.join(".", subArray);
            if (exclusionList.contains(potentialModule)){
                return false;
            }
        }

        // If no matching module found
        return true;
    }

}