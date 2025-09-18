import { spawn } from 'child_process'
import path from 'path'
import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const pythonPath = path.join(process.cwd(), '..', 'venv', 'bin', 'python')
    
    // First, start the complete parallel processing system
    console.log('🏭 Starting complete parallel processing system...')
    const startEverythingPath = path.join(process.cwd(), '..', 'backend', 'start_everything.py')
    
    const startSystemProcess = spawn(pythonPath, [startEverythingPath], {
      cwd: path.join(process.cwd(), '..'),
      env: {
        ...process.env,
      },
    })

    const systemResult = await new Promise<boolean>((resolve) => {
      startSystemProcess.on('close', (code) => {
        resolve(code === 0)
      })
    })

    if (!systemResult) {
      return res.status(500).json({ 
        success: false, 
        message: 'Failed to start parallel processing system. Please ensure Redis is installed and running.' 
      })
    }

    console.log('✅ Parallel processing system is ready, starting scraping task...')
    
    // Now start the scraping task
    const scriptPath = path.join(process.cwd(), '..', 'backend', 'start_scrape_task.py')

    const pythonProcess = spawn(pythonPath, [scriptPath], {
      cwd: path.join(process.cwd(), '..'),
      env: {
        ...process.env,
      },
    })

    let output = ''
    let errorOutput = ''

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString()
      console.log(`Scrape-async stdout: ${data.toString()}`)
    })

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString()
      console.error(`Scrape-async stderr: ${data.toString()}`)
    })

    const result = await new Promise<{ taskId?: string, error?: string }>((resolve) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          const match = output.match(/Task started with ID: ([a-f0-9-]+)/)
          if (match && match[1]) {
            resolve({ taskId: match[1] })
          } else {
            resolve({ error: 'Could not extract task ID from scraper output.' })
          }
        } else {
          resolve({ error: `Scraper process exited with code ${code}: ${errorOutput}` })
        }
      })
    })

    if (result.taskId) {
      res.status(200).json({ 
        success: true, 
        message: 'Parallel scraping task started with multiple workers', 
        task_id: result.taskId 
      })
    } else {
      res.status(500).json({ success: false, message: result.error || 'Failed to start scraping task' })
    }

  } catch (error: any) {
    console.error('Failed to start scraper:', error)
    res.status(500).json({ success: false, message: error.message })
  }
}
