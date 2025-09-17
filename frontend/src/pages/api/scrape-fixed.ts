import { spawn } from 'child_process'
import path from 'path'

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const scraperPath = path.join(process.cwd(), '..', 'scraper.py')
    
    const scraper = spawn('python', [scraperPath], {
      cwd: path.join(process.cwd(), '..'),
      env: {
        ...process.env
      }
    })

    let output = ''
    let errorOutput = ''

    scraper.stdout.on('data', (data) => {
      output += data.toString()
      console.log(`Scraper stdout: ${data.toString()}`)
    })

    scraper.stderr.on('data', (data) => {
      errorOutput += data.toString()
      console.error(`Scraper stderr: ${data.toString()}`)
    })

    await new Promise((resolve, reject) => {
      scraper.on('close', (code) => {
        if (code === 0) {
          resolve(output)
        } else {
          reject(new Error(`Scraper process exited with code ${code}: ${errorOutput}`))
        }
      })
    })

    res.status(200).json({ 
      success: true, 
      message: 'Scraper completed successfully', 
      output 
    })
  } catch (error) {
    console.error('Failed to run scraper:', error)
    res.status(500).json({ 
      success: false, 
      message: error.message 
    })
  }
}
