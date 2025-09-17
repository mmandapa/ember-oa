import { NextApiRequest, NextApiResponse } from 'next'
import { spawn } from 'child_process'
import path from 'path'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    // Path to the simple scraper script
    const scraperPath = path.join(process.cwd(), '..', 'simple_scraper.py')
    
    // Spawn the Python scraper process
    const scraper = spawn('python', [scraperPath], {
      cwd: path.join(process.cwd(), '..'),
      env: {
        ...process.env
      }
    })

    let output = ''
    let errorOutput = ''

    // Capture output
    scraper.stdout.on('data', (data) => {
      output += data.toString()
    })

    scraper.stderr.on('data', (data) => {
      errorOutput += data.toString()
    })

    // Handle process completion
    scraper.on('close', (code) => {
      if (code === 0) {
        res.status(200).json({
          success: true,
          message: 'Scraper completed successfully',
          output: output
        })
      } else {
        res.status(500).json({
          success: false,
          message: 'Scraper failed',
          error: errorOutput,
          output: output
        })
      }
    })

    // Handle process errors
    scraper.on('error', (error) => {
      res.status(500).json({
        success: false,
        message: 'Failed to start scraper',
        error: error.message
      })
    })

  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      error: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}
