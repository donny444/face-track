'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

import "bootstrap/dist/css/bootstrap.min.css";
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap'

import { useSelector } from 'react-redux'
import { RootState } from '../contexts/store'

import { ThemeEnum } from '@/interfaces/enums'
import axios from 'axios';  

export default function RegisterPage() {
  const router = useRouter()
  const theme = useSelector((state: RootState) => state.theme.mode)
  const [formData, setFormData] = useState({
    email: '',
    firstName: '',
    lastName: '',
    password: '',
  })
  const [error, setError] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault()
  try {
    const response = await axios.post("http://localhost:8000/register", {
      email: formData.email,
      first_name: formData.firstName,
      last_name: formData.lastName,
      password: formData.password
    });

    if (response.status === 200) {
      console.log("Register success");
      router.push("/login");
    }
  } catch (error) {
    console.error(error);
    if (axios.isAxiosError(error) && error.response) {
      // ถ้ามี error response จาก server
      setError(error.response.data.error || "Registration failed");
    } else {
      // ถ้าเป็น error อื่นๆ
      setError("Registration failed. Please try again.");
    }
  }
}


  return (
    <Container fluid className={`min-vh-100 ${theme === ThemeEnum.DARK ? 'bg-dark' : 'bg-light'} d-flex align-items-center justify-content-center`}>
      <Row className="w-100 justify-content-center">
        <Col md={6} lg={4}>
          <div className={`${theme === ThemeEnum.DARK ? 'bg-dark text-white' : 'bg-white'} p-4 rounded-lg shadow-sm`}>
            <h2 className={`text-center ${theme === ThemeEnum.DARK ? 'text-white' : 'text-primary'} mb-4`}>
              สมัครสมาชิก
            </h2>
            
            {error && (
              <Alert variant="danger" className="mb-3">
                {error}
              </Alert>
            )}

            <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  อีเมล
                </Form.Label>
                <Form.Control
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  placeholder="กรอกอีเมลของคุณ"
                  required
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  ชื่อ
                </Form.Label>
                <Form.Control
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleChange}
                  placeholder="กรอกชื่อของคุณ"
                  required
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  นามสกุล
                </Form.Label>
                <Form.Control
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleChange}
                  placeholder="กรอกนามสกุลของคุณ"
                  required
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
              </Form.Group>

              <Form.Group className="mb-4">
                <Form.Label className={theme === ThemeEnum.DARK ? 'text-white' : 'text-black'}>
                  รหัสผ่าน
                </Form.Label>
                <Form.Control
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="กรอกรหัสผ่าน"
                  required
                  className={`form-control-lg ${theme === ThemeEnum.DARK ? 'bg-dark text-white' : ''}`}
                />
              </Form.Group>

              <Button 
                variant={theme === ThemeEnum.DARK ? 'light' : 'primary'}
                type="submit" 
                className="w-100 mb-3 py-2"
                size="lg"
              >
                สมัครสมาชิก
              </Button>
            </Form>
          </div>
        </Col>
      </Row>
    </Container>
  )
}