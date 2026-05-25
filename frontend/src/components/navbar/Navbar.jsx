const styles = {
    nav: {
        display: 'flex',
        justifyContent: 'flex-end',
        position: 'fixed',
        backgroundColor: 'transparent',
        top: '20px',
        right: '20px',
        zIndex: 1000,
    },
    button: {
        padding: '0.75rem 1.25rem',
        color: '#ffffff',
        backgroundColor: 'transparent',
        cursor: 'pointer',
        fontWeight: 600,
    },
}

function Navbar({ setView, view, setIsLoginOpen }) {
    return (
        <nav style={styles.nav}>
            <button
                type="button"
                style={styles.button}
                onClick={
                    () => {
                        if(view === 'map') {
                            setIsLoginOpen(true);
                        } else {
                            setView('map');
                        }
                    }
                }
            >
                {view === 'map' ? 'Go to Dashboard' : 'Go to Map'}
            </button>
        </nav>
    )
}

export default Navbar