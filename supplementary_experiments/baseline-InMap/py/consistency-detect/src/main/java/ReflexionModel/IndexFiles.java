package ReflexionModel;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.FileVisitResult;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.SimpleFileVisitor;
import java.nio.file.attribute.BasicFileAttributes;

import org.apache.lucene.analysis.Analyzer;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.StringField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;

public class IndexFiles
{
    String indexPath;
    String docsPath;
    boolean createIndex;

    public IndexFiles() {}

    /** Index all text files under a directory. */
    public void indexFiles( String indexPath, String docsPath, String sourceFileExt,String project )
    {
        //System.out.println( "\n\nINDEXING\n--------" );
        this.indexPath = indexPath;
        this.docsPath = docsPath;
        createIndex = true;

        if ( docsPath == null )
        {
            System.err.println( "Docs path is null" );
            System.exit( 1 );
        }

        final Path docDir = Paths.get( docsPath );

        if ( !Files.isReadable( docDir ) )
        {
            System.out.println( "Document directory '" + docDir.toAbsolutePath() + "' does not exist or is not readable, please check the path" );
            System.exit( 1 );
        }

        //Date start = new Date();

        try
        {
            //System.out.println( "\nIndexing docs" );
            //System.out.println( " in " + docsPath );
            //System.out.println( " to " + indexPath );

            Directory dir = FSDirectory.open( Paths.get( indexPath ) );
            Analyzer analyzer = new StandardAnalyzer();
            IndexWriterConfig iwc = new IndexWriterConfig( analyzer );

            if( createIndex )
            {
                // Create a new index in the directory, removing any previously indexed documents:
                iwc.setOpenMode( OpenMode.CREATE );
            }
            else
            {
                // Add new documents to an existing index:
                iwc.setOpenMode( OpenMode.CREATE_OR_APPEND );
            }

            // Optional: for better indexing performance, if you are indexing many documents, increase the RAM
            // buffer.  But if you do this, increase the max heap size to the JVM (e.g. add -Xmx512m or -Xmx1g):
            // iwc.setRAMBufferSizeMB(256.0);

            IndexWriter writer = new IndexWriter( dir, iwc );
            indexDocs( writer, docDir, sourceFileExt,project );

            // NOTE: if you want to maximize search performance, you can optionally call forceMerge here.  This can be a terribly costly operation, so generally it's only
            // worth it when your index is relatively static (ie you're done adding documents to it):
            // writer.forceMerge(1);

            writer.close();

            //Date end = new Date();
            //String timeTaken = String.valueOf( end.getTime() - start.getTime() );
            //System.out.printf( "\nTime Taken: " + timeTaken + " total milliseconds\n" );

        }
        catch( FileNotFoundException ex )
        {
            System.out.println( "Unable to open files '" + docsPath + "'" );
        }
        catch ( IOException ex )
        {
            System.out.println (" caught a " + ex.getClass() + "\n with message: " + ex.getMessage() );
        }
        catch( Exception ex )
        {
            ex.printStackTrace();
        }
    }

    /**
     * Indexes the given file using the given writer, or if a directory is given,
     * recurses over files and directories found under the given directory.
     *
     * NOTE: This method indexes one document per input file.  This is slow.  For good
     * throughput, put multiple documents into your input file(s).  An example of this is
     * in the benchmark module, which can create "line doc" files, one document per line,
     * using the
     * <a href="../../../../../contrib-benchmark/org/apache/lucene/benchmark/byTask/tasks/WriteLineDocTask.html"
     * >WriteLineDocTask</a>.
     *
     * @param writer Writer to the index where the given file/dir info will be stored
     * @param path The file to index, or the directory to recurse into to find files to index
     * @throws IOException If there is a low-level I/O error
     */
    static void indexDocs( final IndexWriter writer, Path path, String sourceFileExt ,String project) throws IOException
    {
        if( Files.isDirectory( path ) )
        {
            Files.walkFileTree( path, new SimpleFileVisitor<Path>()
            {
                @Override
                public FileVisitResult visitFile( Path file, BasicFileAttributes attrs ) throws IOException
                {
                    try
                    {
                        indexDoc( writer, file, attrs.lastModifiedTime().toMillis(), sourceFileExt,project );
                    }
                    catch( IOException ignore )
                    {
                        // don't index files that can't be read.
                    }

                    return FileVisitResult.CONTINUE;
                }
            });
        }
        else
        {
            indexDoc( writer, path, Files.getLastModifiedTime( path ).toMillis(), sourceFileExt ,project);
        }
    }

    /** Indexes a single document */
    static void indexDoc( IndexWriter writer, Path file, long lastModified, String sourceFileExt,String project) throws IOException
    {
        if( file.toString().endsWith( sourceFileExt ) )		// index only files with the correct file type
        {
            try( InputStream stream = Files.newInputStream( file ) )
            {
                // make a new, empty document
                Document doc = new Document();

                // Add the path of the file as a field named "path".  Use a
                // field that is indexed (i.e. searchable), but don't tokenize
                // the field into separate words and don't index term frequency
                // or positional information:
                Field pathField = new StringField( "path", file.toString().substring(file.toString().indexOf(project)+project.length()+1), Field.Store.YES );
                doc.add( pathField );

                // Add the contents of the file to a field named "contents".  Specify a Reader,
                // so that the text of the file is tokenized and indexed, but not stored.
                // Note that FileReader expects the file to be in UTF-8 encoding.
                // If that's not the case searching for special characters will fail.
                Field contentsField = new TextField( "contents", new BufferedReader( new InputStreamReader( stream, StandardCharsets.UTF_8 ) ) );
                doc.add( contentsField );

                if ( writer.getConfig().getOpenMode() == OpenMode.CREATE )
                {
                    // New index, so we just add the document (no old document can be there):
                    //System.out.println("adding " + file);
                    writer.addDocument( doc );
                }
                else
                {
                    // Existing index (an old copy of this document may have been indexed) so
                    // we use updateDocument instead to replace the old one matching the exact
                    // path, if present:
                    //System.out.println( "updating " + file );
                    writer.updateDocument( new Term( "path", file.toString() ), doc );
                }
            }
        }
    }

}
