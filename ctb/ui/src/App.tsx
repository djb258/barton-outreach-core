const App = () => {
  console.log('APP IS RENDERING - CHECK CONSOLE');
  
  return (
    <div style={{
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '12px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.1)',
        maxWidth: '600px',
        textAlign: 'center'
      }}>
        <h1 style={{ color: '#333', fontSize: '32px', marginBottom: '16px' }}>
          ✅ App is Running!
        </h1>
        <p style={{ color: '#666', fontSize: '18px', marginBottom: '24px' }}>
          If you can see this message, React and Vite are working correctly.
        </p>
        <div style={{ background: '#f0f0f0', padding: '20px', borderRadius: '8px' }}>
          <p style={{ color: '#333', margin: 0 }}>
            Check your browser console for the log message.
          </p>
        </div>
      </div>
    </div>
  );
};

export default App;
