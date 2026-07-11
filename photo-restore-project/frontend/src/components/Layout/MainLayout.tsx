import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar, MobileNav } from './Sidebar'
import { Footer } from './Footer'

/** Layout principal: Header arriba, Sidebar a la izquierda (escritorio) o barra
 * inferior (móvil), contenido y Footer. */
export function MainLayout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        {/* pb en móvil para no tapar contenido con la barra inferior */}
        <main className="flex-1 p-4 pb-24 sm:p-6 md:pb-6">
          <Outlet />
        </main>
      </div>
      <div className="hidden md:block">
        <Footer />
      </div>
      <MobileNav />
    </div>
  )
}
