import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../providers/auth_provider.dart';
import '../services/auth_service.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();

  final _firstNameController = TextEditingController();

  final _lastNameController = TextEditingController();

  final _emailController = TextEditingController();

  final _phoneController = TextEditingController();

  final _passwordController = TextEditingController();

  final _confirmPasswordController = TextEditingController();

  final _scholarIdController = TextEditingController();

  final _institutionController = TextEditingController();

  final _programController = TextEditingController();

  final _studyLevelController = TextEditingController();

  final _graduationYearController = TextEditingController();

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _scholarIdController.dispose();
    _institutionController.dispose();
    _programController.dispose();
    _studyLevelController.dispose();
    _graduationYearController.dispose();

    super.dispose();
  }

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final graduationYear = int.tryParse(_graduationYearController.text.trim());

    if (graduationYear == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a valid graduation year.')),
      );

      return;
    }

    try {
      await AuthService.register(
        email: _emailController.text,
        password: _passwordController.text,
        passwordConfirmation: _confirmPasswordController.text,
        firstName: _firstNameController.text,
        lastName: _lastNameController.text,
        phone: _phoneController.text,
        scholarId: _scholarIdController.text,
        institution: _institutionController.text,
        country: 'RW',
        program: _programController.text,
        studyLevel: _studyLevelController.text,
        graduationYear: graduationYear,
      );

      await ref
          .read(authProvider.notifier)
          .login(
            email: _emailController.text,
            password: _passwordController.text,
          );

      final authState = ref.read(authProvider);
      if (authState.status != AuthStatus.authenticated) {
        throw (authState.error ??
            'Account created, but automatic login failed.');
      }

      if (mounted) {
        context.go('/');
      }
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const Text(
                'Scholar registration',
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 8),

              const Text('Create your MasterSave account.'),

              const SizedBox(height: 24),

              _field(controller: _firstNameController, label: 'First name'),

              _field(controller: _lastNameController, label: 'Last name'),

              _field(
                controller: _emailController,
                label: 'Email',
                keyboardType: TextInputType.emailAddress,
              ),

              _field(
                controller: _phoneController,
                label: 'Phone number',
                keyboardType: TextInputType.phone,
              ),

              _field(
                controller: _passwordController,
                label: 'Password',
                obscureText: true,
              ),

              _field(
                controller: _confirmPasswordController,
                label: 'Confirm password',
                obscureText: true,
              ),

              const SizedBox(height: 12),

              const Text(
                'Scholar information',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),

              const SizedBox(height: 16),

              _field(controller: _scholarIdController, label: 'Scholar ID'),

              _field(controller: _institutionController, label: 'Institution'),

              _field(controller: _programController, label: 'Program'),

              _field(controller: _studyLevelController, label: 'Study level'),

              _field(
                controller: _graduationYearController,
                label: 'Graduation year',
                keyboardType: TextInputType.number,
              ),

              const SizedBox(height: 20),

              ElevatedButton(
                onPressed: _register,
                child: const Text('Create account'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _field({
    required TextEditingController controller,
    required String label,
    TextInputType? keyboardType,
    bool obscureText = false,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextFormField(
        controller: controller,
        keyboardType: keyboardType,
        obscureText: obscureText,
        decoration: InputDecoration(labelText: label),
        validator: (value) {
          if (value == null || value.trim().isEmpty) {
            return '$label is required.';
          }

          return null;
        },
      ),
    );
  }
}
